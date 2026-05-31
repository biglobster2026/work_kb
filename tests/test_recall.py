from work_kb.models import Item, Tier
from work_kb.recall import rank, tokenize

ITEMS = [
    Item(slug="auth", tier=Tier.DETAIL, title="Auth retry uses jitter", tags=["auth"]),
    Item(slug="db", tier=Tier.DETAIL, title="Database pool sizing", body="connections and pools"),
    Item(slug="cache", tier=Tier.ARTIFACT, title="Cache TTL note", project="acme"),
]


def test_tokenize():
    assert tokenize("Auth-Retry, 9x!") == ["auth", "retry", "9x"]


def test_rank_obvious_match_first():
    hits = rank("auth jitter retry", ITEMS)
    assert hits[0].item.slug == "auth"


def test_rank_matches_body():
    hits = rank("connection pools", ITEMS)
    assert hits[0].item.slug == "db"


def test_rank_matches_project_field():
    hits = rank("acme", ITEMS, limit=1)
    assert hits[0].item.slug == "cache"


def test_rank_empty_items():
    assert rank("anything", []) == []


def test_rank_no_match_scores_zero():
    hits = rank("xyzzy", ITEMS)
    assert all(h.score == 0.0 for h in hits)


def test_rank_respects_limit():
    assert len(rank("a", ITEMS, limit=1)) == 1
