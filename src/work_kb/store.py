"""The filesystem layer — the one place that touches disk.

Maps tiers to directories, reads every item into memory (the corpus is large but
the *records* are small), writes items, and writes the generated navigation
files produced by ``build``. Foundation items live flat (there are ~100);
detail and artifact items are sharded into 256 buckets by slug.
"""

from __future__ import annotations

from pathlib import Path

from work_kb.models import Item, Tier, parse_item, shard

# Tiers whose item dirs are sharded (too many files for one directory).
_SHARDED = {Tier.DETAIL, Tier.ARTIFACT}


class Store:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.kb = self.root / "kb"

    # --- paths -------------------------------------------------------------

    def tier_dir(self, tier: Tier) -> Path:
        return self.kb / tier.dirname

    def item_path(self, item: Item) -> Path:
        base = self.tier_dir(item.tier) / "items"
        if item.tier in _SHARDED:
            base = base / shard(item.slug)
        return base / f"{item.slug}.md"

    # --- read --------------------------------------------------------------

    def read_all(self) -> list[Item]:
        """Every item across every tier. Slug collisions are NOT resolved here
        (``validate`` reports them); the on-disk filename stem is the fallback
        slug when frontmatter omits one."""
        items: list[Item] = []
        for tier in Tier:
            items_root = self.tier_dir(tier) / "items"
            if not items_root.exists():
                continue
            for path in sorted(items_root.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                items.append(parse_item(text, fallback_slug=path.stem))
        return items

    def find(self, slug: str) -> tuple[Item, Path] | None:
        for tier in Tier:
            items_root = self.tier_dir(tier) / "items"
            if not items_root.exists():
                continue
            for path in items_root.rglob(f"{slug}.md"):
                return parse_item(path.read_text(encoding="utf-8"), fallback_slug=slug), path
        return None

    # --- write -------------------------------------------------------------

    def write_item(self, item: Item) -> Path:
        path = self.item_path(item)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item.to_markdown(), encoding="utf-8")
        return path

    def move_item(self, item: Item, new_tier: Tier) -> Path:
        """Re-tier an item: delete the old file, write under the new tier."""
        old = self.item_path(item)
        item.tier = new_tier
        new_path = self.write_item(item)
        if old.exists() and old != new_path:
            old.unlink()
        return new_path

    def write_generated(self, files: dict[str, str]) -> list[Path]:
        """Write the build output. Keys are repo-root-relative paths."""
        written: list[Path] = []
        for relpath, content in files.items():
            path = self.root / relpath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            written.append(path)
        return written
