"""Tests for the knowledge-tree overview. The renderer is pure, so we assert on
the produced HTML/SVG string — geometry, encoding rules, and the non-enumeration
discipline (artifacts must NOT appear as individual nodes)."""

from work_kb.models import Item, Tier
from work_kb.viz import (
    _artifact_clusters,
    _build_nodes,
    _detail_clusters,
    _heat,
    render_overview_html,
)

F = [
    Item(slug="mission", tier=Tier.FOUNDATION, title="Project mission", tags=["overview"]),
    Item(slug="north-star", tier=Tier.FOUNDATION, title="North star metric"),
]
D = [
    Item(slug="auth-jitter", tier=Tier.DETAIL, title="Auth jitter", tags=["auth"]),
    Item(slug="auth-tokens", tier=Tier.DETAIL, title="Token rotation", tags=["auth"]),
    Item(slug="db-pool", tier=Tier.DETAIL, title="DB pool", tags=["db"]),
]
A = [
    Item(slug="l1", tier=Tier.ARTIFACT, title="Log 1", project="acme"),
    Item(slug="l2", tier=Tier.ARTIFACT, title="Log 2", project="acme"),
    Item(slug="n1", tier=Tier.ARTIFACT, title="Note 1", project="beta"),
]


def test_renders_self_contained_html():
    out = render_overview_html(F + D + A)
    assert out.startswith("<!DOCTYPE html>")
    assert "<svg" in out and "</svg>" in out
    # No external resource requests — must work offline.
    assert "http://" not in out.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "https://" not in out
    assert "<script src" not in out and "<link" not in out


def test_brand_orange_present():
    assert "#E8650A" in render_overview_html(F + D + A)


def test_counts_in_chips():
    out = render_overview_html(F + D + A)
    assert ">2<" in out  # foundation count
    assert "Total <b>8</b>" in out


def test_detail_clusters_group_by_tag_sorted_by_size():
    clusters = _detail_clusters(D)
    assert clusters[0][0] == "auth"  # 2 items, comes first
    assert len(clusters[0][1]) == 2


def test_artifact_clusters_group_by_project():
    clusters = _artifact_clusters(A)
    assert clusters[0] == ("acme", 2)
    assert ("beta", 1) in clusters


def test_artifacts_not_enumerated_as_nodes():
    # The cardinal rule: artifact ITEM titles must never appear in the SVG.
    out = render_overview_html(F + D + A)
    assert "Log 1" not in out and "Log 2" not in out and "Note 1" not in out
    # But their project clusters DO appear.
    assert "acme" in out and "beta" in out


def test_foundation_items_are_individual_nodes():
    out = render_overview_html(F + D + A)
    assert "Project mission" in out  # small tier -> enumerated with labels


def test_heat_monotonic():
    lo = _heat(1, 10)
    hi = _heat(10, 10)
    assert lo != hi
    assert _heat(0, 10) == _heat(0, 10)  # deterministic


def test_build_nodes_radii_increase_by_tier():
    nodes, meta = _build_nodes(F + D + A)
    assert meta["tiers"]["foundation"] < meta["tiers"]["detail"] < meta["tiers"]["artifact"]


def test_build_nodes_has_root_and_panel():
    nodes, meta = _build_nodes(F + D + A)
    assert nodes[0].kind == "root"
    assert "d:auth" in meta["panel"]
    assert meta["panel"]["d:auth"]["count"] == 2
    assert "a:acme" in meta["panel"]


def test_panel_detail_lists_member_items():
    _, meta = _build_nodes(D)
    auth = meta["panel"]["d:auth"]
    titles = {m["title"] for m in auth["items"]}
    assert titles == {"Auth jitter", "Token rotation"}


def test_panel_artifact_carries_search_query_not_items():
    _, meta = _build_nodes(A)
    acme = meta["panel"]["a:acme"]
    assert acme["query"] == "project: acme"
    assert "items" not in acme  # never list artifact contents


def test_empty_kb_still_renders():
    out = render_overview_html([])
    assert out.startswith("<!DOCTYPE html>")
    assert "Total <b>0</b>" in out


def test_large_foundation_drops_labels_but_keeps_nodes():
    big = [Item(slug=f"f{i}", tier=Tier.FOUNDATION, title=f"Fact {i}") for i in range(40)]
    nodes, _ = _build_nodes(big)
    item_nodes = [n for n in nodes if n.kind == "item"]
    assert len(item_nodes) == 40
    assert all(n.label == "" for n in item_nodes)  # too many to label legibly
