from work_kb.build import (
    build,
    render_artifact_manifest,
    render_copilot_instructions,
    render_detail_index,
    render_foundation_index,
    render_tag_pages,
)
from work_kb.models import Item, Tier

F = [Item(slug="mission", tier=Tier.FOUNDATION, title="Project mission", tags=["overview"])]
D = [
    Item(slug="auth-jitter", tier=Tier.DETAIL, title="Auth jitter", tags=["auth"]),
    Item(slug="db-pool", tier=Tier.DETAIL, title="DB pool sizing", tags=["db", "perf"]),
]
A = [Item(slug="log-2026", tier=Tier.ARTIFACT, title="Log excerpt", project="acme")]


def test_foundation_index_enumerates_titles():
    out = render_foundation_index(F)
    assert "Project mission" in out
    assert "read this whole file" in out


def test_foundation_index_empty():
    assert "No foundational items" in render_foundation_index([])


def test_detail_index_is_topic_map_not_flat_list():
    out = render_detail_index(D)
    # It lists topics with counts, links to by-tag pages — not the items inline.
    assert "by-tag/auth.md" in out
    assert "by-tag/perf.md" in out
    assert "(1)" in out


def test_tag_pages_one_per_tag():
    # render_tag_pages keys are relative to kb/; build() prefixes them with kb/.
    pages = render_tag_pages(D)
    assert "10-details/by-tag/auth.md" in pages
    assert "10-details/by-tag/db.md" in pages
    assert "DB pool sizing" in pages["10-details/by-tag/perf.md"]


def test_artifact_manifest_does_not_enumerate():
    out = render_artifact_manifest(A)
    assert "NOT enumerated" in out
    # The artifact title must NOT appear — retrieval is grep, not a listing.
    assert "Log excerpt" not in out
    assert "acme" in out  # but projects present are summarized


def test_copilot_instructions_carry_counts():
    out = render_copilot_instructions({Tier.FOUNDATION: 1, Tier.DETAIL: 2, Tier.ARTIFACT: 1})
    assert "(1 items)" in out
    assert "kb/00-foundation/INDEX.md" in out
    assert "SEARCH" in out


def test_build_produces_all_core_files():
    files = build(F + D + A)
    assert "kb/00-foundation/INDEX.md" in files
    assert "kb/10-details/INDEX.md" in files
    assert "kb/20-artifacts/MANIFEST.md" in files
    assert ".github/copilot-instructions.md" in files
    assert "AGENTS.md" in files
    assert "kb/10-details/by-tag/auth.md" in files


def test_build_is_deterministic():
    assert build(F + D + A) == build(A + D + F)


def test_build_empty_kb():
    files = build([])
    assert "No foundational items" in files["kb/00-foundation/INDEX.md"]
