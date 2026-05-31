from datetime import date

import pytest

from work_kb.models import Item, Tier, parse_item, shard, slugify


def test_slugify_basic():
    assert slugify("Why the Auth Retry Uses Jitter!") == "why-the-auth-retry-uses-jitter"


def test_slugify_empty_falls_back():
    assert slugify("   ") == "untitled"


def test_tier_dirname_and_roundtrip():
    assert Tier.FOUNDATION.dirname == "00-foundation"
    assert Tier.from_str("DETAIL") is Tier.DETAIL


def test_tier_unknown_raises():
    with pytest.raises(ValueError, match="unknown tier"):
        Tier.from_str("legendary")


def test_shard_is_two_hex_and_stable():
    s = shard("some-slug")
    assert len(s) == 2 and all(c in "0123456789abcdef" for c in s)
    assert shard("some-slug") == s


def test_item_to_markdown_and_back():
    it = Item(
        slug="auth-jitter",
        tier=Tier.DETAIL,
        title="Auth retry uses jitter",
        body="Because thundering herds.",
        tags=["auth", "reliability"],
        project="acme",
        created=date(2026, 5, 31),
        links=["retry-policy"],
    )
    text = it.to_markdown()
    back = parse_item(text)
    assert back == it


def test_to_markdown_omits_empty_optionals():
    it = Item(slug="x", tier=Tier.FOUNDATION, title="X")
    text = it.to_markdown()
    assert "tags" not in text and "project" not in text and "links" not in text


def test_parse_requires_frontmatter():
    with pytest.raises(ValueError, match="frontmatter"):
        parse_item("no frontmatter here")


def test_parse_uses_fallback_slug():
    text = "---\ntier: detail\ntitle: T\n---\nbody"
    it = parse_item(text, fallback_slug="from-filename")
    assert it.slug == "from-filename"


def test_parse_missing_tier_raises():
    with pytest.raises(ValueError, match="tier"):
        parse_item("---\nslug: s\ntitle: T\n---\n", fallback_slug="s")


def test_parse_body_stripped():
    it = parse_item("---\nslug: s\ntier: detail\ntitle: T\n---\n\n  hi  \n", fallback_slug="s")
    assert it.body == "hi"
