"""Lexical BM25 ranking — pure stdlib, zero dependencies.

The KB's primary retrieval is the *agent's own* file search; this scorer exists
only for the optional ``kb pack`` command, which assembles a single CONTEXT.md
for agents that can't browse files themselves. Same brute-force-over-a-small-set
reasoning as everywhere else: at pack time you grep to a candidate set first,
then rank those — never the whole 50k corpus.

Lifted from the life_ops memory recall module (same BM25, adapted to Items).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from work_kb.models import Item

BM25_K1 = 1.5
BM25_B = 0.75
_TOKEN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Hit:
    item: Item
    score: float


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _doc_text(item: Item) -> str:
    """What we score over: title + tags + project carry strong signal, so weight
    them by inclusion alongside the body."""
    parts = [item.title, " ".join(item.tags), item.project or "", item.body]
    return " ".join(p for p in parts if p)


def rank(query: str, items: list[Item], *, limit: int = 10) -> list[Hit]:
    """BM25 over the given items, highest first. IDF/lengths computed per call —
    fine, because callers pass a pre-filtered candidate set, not the whole KB."""
    if not items:
        return []
    docs = [tokenize(_doc_text(it)) for it in items]
    n = len(docs)
    avg_len = sum(len(d) for d in docs) / n

    df: Counter[str] = Counter()
    for d in docs:
        df.update(set(d))
    idf = {term: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}

    q_terms = set(tokenize(query))
    hits: list[Hit] = []
    for item, doc in zip(items, docs, strict=True):
        tf = Counter(doc)
        dl = len(doc)
        score = 0.0
        for term in q_terms:
            f = tf.get(term, 0)
            if not f:
                continue
            num = f * (BM25_K1 + 1.0)
            den = f + BM25_K1 * (1.0 - BM25_B + BM25_B * dl / avg_len)
            score += idf.get(term, 0.0) * num / den
        hits.append(Hit(item, score))

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]
