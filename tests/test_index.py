"""Tests for the machine-readable kb/index.json catalog. Pure dict output."""

import json

from work_kb.index import SCHEMA_VERSION, build_index, render_index_json
from work_kb.models import Item, Tier

F = [Item(slug="mission", tier=Tier.FOUNDATION, title="Mission", tags=["overview"])]
D = [
    Item(slug="auth-jitter", tier=Tier.DETAIL, title="Auth jitter", tags=["auth"]),
    Item(slug="db-pool", tier=Tier.DETAIL, title="DB pool", tags=["db", "perf"]),
]
A = [
    Item(slug="l1", tier=Tier.ARTIFACT, title="Log 1", project="acme"),
    Item(slug="l2", tier=Tier.ARTIFACT, title="Log 2", project="acme"),
]


def test_schema_version_and_counts():
    idx = build_index(F + D + A)
    assert idx["schema_version"] == SCHEMA_VERSION
    assert idx["counts"] == {"foundation": 1, "detail": 2, "artifact": 2}


def test_retrieval_modes_per_tier():
    idx = build_index(F + D + A)
    assert idx["tiers"]["foundation"]["retrieval"] == "load-all"
    assert idx["tiers"]["detail"]["retrieval"] == "navigate"
    assert idx["tiers"]["artifact"]["retrieval"] == "search"


def test_foundation_and_detail_items_listed_with_paths():
    idx = build_index(F + D + A)
    fnd = idx["tiers"]["foundation"]["items"]
    assert fnd[0]["path"] == "kb/00-foundation/items/mission.md"
    det = {i["slug"]: i["path"] for i in idx["tiers"]["detail"]["items"]}
    assert det["auth-jitter"].startswith("kb/10-details/items/")
    assert det["auth-jitter"].endswith("/auth-jitter.md")


def test_detail_topics_summarized():
    idx = build_index(F + D + A)
    topics = {t["tag"]: t["count"] for t in idx["tiers"]["detail"]["topics"]}
    assert topics == {"auth": 1, "db": 1, "perf": 1}


def test_artifacts_clustered_not_enumerated():
    idx = build_index(F + D + A)
    art = idx["tiers"]["artifact"]
    # No item list — only project clusters + a search root.
    assert "items" not in art
    assert art["search_root"] == "kb/20-artifacts/items/"
    clusters = {c["project"]: c["count"] for c in art["clusters"]}
    assert clusters == {"acme": 2}
    # The cardinal rule: artifact titles never appear in the catalog.
    blob = json.dumps(idx)
    assert "Log 1" not in blob and "Log 2" not in blob


def test_render_is_valid_json():
    parsed = json.loads(render_index_json(F + D + A))
    assert parsed["counts"]["detail"] == 2


def test_empty_kb_renders():
    idx = build_index([])
    assert idx["counts"] == {"foundation": 0, "detail": 0, "artifact": 0}
