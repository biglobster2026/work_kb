from work_kb.models import Item, Tier
from work_kb.store import Store


def _item(slug, tier, title="T"):
    return Item(slug=slug, tier=tier, title=title)


def test_write_and_read_roundtrip(tmp_path):
    store = Store(tmp_path)
    store.write_item(_item("a", Tier.FOUNDATION))
    store.write_item(_item("b", Tier.DETAIL))
    store.write_item(_item("c", Tier.ARTIFACT))
    slugs = {it.slug for it in store.read_all()}
    assert slugs == {"a", "b", "c"}


def test_foundation_is_flat_detail_is_sharded(tmp_path):
    store = Store(tmp_path)
    fp = store.write_item(_item("found", Tier.FOUNDATION))
    dp = store.write_item(_item("deet", Tier.DETAIL))
    assert fp.parent.name == "items"  # flat
    assert dp.parent.parent.name == "items"  # items/<shard>/file.md


def test_find_returns_item_and_path(tmp_path):
    store = Store(tmp_path)
    store.write_item(_item("needle", Tier.DETAIL, title="Find me"))
    found = store.find("needle")
    assert found is not None
    item, path = found
    assert item.title == "Find me"
    assert path.exists()


def test_find_missing_returns_none(tmp_path):
    assert Store(tmp_path).find("ghost") is None


def test_move_item_deletes_old_file(tmp_path):
    store = Store(tmp_path)
    old = store.write_item(_item("rising", Tier.DETAIL))
    store.move_item(store.find("rising")[0], Tier.FOUNDATION)
    assert not old.exists()
    item, _ = store.find("rising")
    assert item.tier is Tier.FOUNDATION


def test_write_generated(tmp_path):
    store = Store(tmp_path)
    store.write_generated({"AGENTS.md": "hi", "kb/x/INDEX.md": "yo"})
    assert (tmp_path / "AGENTS.md").read_text() == "hi"
    assert (tmp_path / "kb" / "x" / "INDEX.md").read_text() == "yo"


def test_read_all_empty(tmp_path):
    assert Store(tmp_path).read_all() == []
