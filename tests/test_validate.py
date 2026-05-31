from work_kb.models import Item, Tier
from work_kb.validate import Level, validate


def _i(slug, tier=Tier.DETAIL, links=None):
    return Item(slug=slug, tier=tier, title=slug, links=links or [])


def test_clean_kb_has_no_findings():
    assert validate([_i("a"), _i("b")]) == []


def test_duplicate_slug_is_error():
    findings = validate([_i("dup"), _i("dup")])
    assert any(f.level is Level.ERROR and "duplicate" in f.message for f in findings)


def test_dangling_link_is_error():
    findings = validate([_i("a", links=["nope"])])
    assert any(f.level is Level.ERROR and "unknown slug" in f.message for f in findings)


def test_valid_link_passes():
    assert validate([_i("a", links=["b"]), _i("b")]) == []


def test_foundation_soft_cap_warns():
    items = [_i(f"f{n}", tier=Tier.FOUNDATION) for n in range(115)]
    findings = validate(items)
    warn = [f for f in findings if f.level is Level.WARN]
    assert warn and "foundation" in warn[0].message
    assert "dump-able" in warn[0].message


def test_artifact_tier_never_caps():
    items = [_i(f"a{n}", tier=Tier.ARTIFACT) for n in range(500)]
    assert all(f.level is not Level.WARN for f in validate(items))
