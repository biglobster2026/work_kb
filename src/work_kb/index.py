"""The machine-readable catalog — `kb/index.json`.

A single structured document any tool or agent can ingest to understand the KB
without parsing markdown: tier counts, each tier's retrieval mode, item paths,
and the topic/project clusters. This is what lets work_kb grow past "files an
agent reads" into "a KB a program can query."

It honors the same non-enumeration rule as the rest of the system: foundation
and detail items are listed (they are browsable tiers), but artifacts are
summarized as project clusters with counts and a search root — never enumerated,
because the tier can hold tens of thousands.

Pure: items in, a JSON string out. No I/O.
"""

from __future__ import annotations

import json
from collections import defaultdict

from work_kb.models import Item, Tier, shard

# Bump when the JSON shape changes so consumers can guard on it.
SCHEMA_VERSION = 1


def _foundation_entries(items: list[Item]) -> list[dict]:
    return [
        {
            "slug": it.slug,
            "title": it.title,
            "tags": it.tags,
            "project": it.project,
            "path": f"kb/{Tier.FOUNDATION.dirname}/items/{it.slug}.md",
            "links": it.links,
        }
        for it in sorted(items, key=lambda i: (i.title.lower(), i.slug))
    ]


def _detail_entries(items: list[Item]) -> tuple[list[dict], list[dict]]:
    by_tag: dict[str, int] = defaultdict(int)
    entries: list[dict] = []
    for it in sorted(items, key=lambda i: (i.title.lower(), i.slug)):
        for tag in it.tags:
            by_tag[tag] += 1
        entries.append(
            {
                "slug": it.slug,
                "title": it.title,
                "tags": it.tags,
                "project": it.project,
                "path": f"kb/{Tier.DETAIL.dirname}/items/{shard(it.slug)}/{it.slug}.md",
                "links": it.links,
            }
        )
    topics = [
        {"tag": tag, "count": n, "path": f"kb/{Tier.DETAIL.dirname}/by-tag/{tag}.md"}
        for tag, n in sorted(by_tag.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    return topics, entries


def _artifact_clusters(items: list[Item]) -> list[dict]:
    by_proj: dict[str, int] = defaultdict(int)
    for it in items:
        by_proj[it.project or "(no project)"] += 1
    return [
        {"project": proj, "count": n}
        for proj, n in sorted(by_proj.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def build_index(items: list[Item]) -> dict:
    """The catalog as a plain dict (so it is easy to assert on in tests)."""
    by_tier: dict[Tier, list[Item]] = {t: [] for t in Tier}
    for it in items:
        by_tier[it.tier].append(it)

    topics, detail_items = _detail_entries(by_tier[Tier.DETAIL])

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "kb build",
        "counts": {t.value: len(by_tier[t]) for t in Tier},
        "tiers": {
            "foundation": {
                "retrieval": "load-all",
                "index": f"kb/{Tier.FOUNDATION.dirname}/INDEX.md",
                "items": _foundation_entries(by_tier[Tier.FOUNDATION]),
            },
            "detail": {
                "retrieval": "navigate",
                "index": f"kb/{Tier.DETAIL.dirname}/INDEX.md",
                "topics": topics,
                "items": detail_items,
            },
            "artifact": {
                "retrieval": "search",
                "search_root": f"kb/{Tier.ARTIFACT.dirname}/items/",
                "clusters": _artifact_clusters(by_tier[Tier.ARTIFACT]),
            },
        },
    }


def render_index_json(items: list[Item]) -> str:
    """The catalog serialized as pretty JSON (stable key order, UTF-8)."""
    return json.dumps(build_index(items), ensure_ascii=False, indent=2) + "\n"
