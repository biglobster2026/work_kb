"""The canonical data model: a knowledge-base ``Item`` and its three ``Tier``s.

Every item is one markdown file with YAML frontmatter and a body — the same
one-fact-per-file shape used elsewhere, so files stay human-editable and
git-diffable. This module is pure: parse text in, serialize text out, no I/O.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

import yaml


class Tier(StrEnum):
    """The three tiers. The value is the on-disk directory prefix, and the
    ordering encodes "how always-relevant" — foundation is loaded every time,
    artifacts only when searched."""

    FOUNDATION = "foundation"
    DETAIL = "detail"
    ARTIFACT = "artifact"

    @property
    def dirname(self) -> str:
        return {
            Tier.FOUNDATION: "00-foundation",
            Tier.DETAIL: "10-details",
            Tier.ARTIFACT: "20-artifacts",
        }[self]

    @classmethod
    def from_str(cls, s: str) -> Tier:
        try:
            return cls(s.strip().lower())
        except ValueError as exc:
            valid = ", ".join(t.value for t in cls)
            raise ValueError(f"unknown tier {s!r}; expected one of: {valid}") from exc


# Soft caps. These don't block writes — `validate` warns when a tier nears them.
# The foundation cap is the load-bearing one: tier 1 must stay small enough to
# dump into an agent's context wholesale (the same discipline as a memory tier's
# forgetting curve, enforced by review instead of eviction).
SOFT_CAPS: dict[Tier, int] = {
    Tier.FOUNDATION: 120,
    Tier.DETAIL: 12_000,
    Tier.ARTIFACT: 0,  # 0 == unbounded
}

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def slugify(title: str) -> str:
    """A filesystem- and link-safe slug. Deterministic; dumb on purpose."""
    s = _SLUG_STRIP.sub("-", title.strip().lower()).strip("-")
    return s or "untitled"


def shard(slug: str) -> str:
    """Two-hex-char bucket for a slug, so detail/artifact tiers spread across
    256 directories instead of piling 50k files into one (keeps git and the
    filesystem fast)."""
    return hashlib.sha1(slug.encode("utf-8")).hexdigest()[:2]


@dataclass
class Item:
    """One knowledge-base entry. ``slug`` is the stable identifier and the
    filename stem; cross-references in ``links`` are slugs."""

    slug: str
    tier: Tier
    title: str
    body: str = ""
    tags: list[str] = field(default_factory=list)
    project: str | None = None
    created: date | None = None
    links: list[str] = field(default_factory=list)

    def frontmatter(self) -> dict:
        """The YAML header as a plain dict, omitting empty optionals."""
        fm: dict = {
            "slug": self.slug,
            "tier": self.tier.value,
            "title": self.title,
        }
        if self.tags:
            fm["tags"] = self.tags
        if self.project:
            fm["project"] = self.project
        if self.created:
            fm["created"] = self.created.isoformat()
        if self.links:
            fm["links"] = self.links
        return fm

    def to_markdown(self) -> str:
        header = yaml.safe_dump(self.frontmatter(), sort_keys=False).strip()
        body = self.body.strip()
        return f"---\n{header}\n---\n\n{body}\n" if body else f"---\n{header}\n---\n"


def parse_item(text: str, *, fallback_slug: str | None = None) -> Item:
    """Parse a markdown file's text into an ``Item``. ``fallback_slug`` is used
    when the frontmatter omits ``slug`` (e.g. derived from the filename)."""
    m = _FRONTMATTER.match(text)
    if not m:
        raise ValueError("item is missing a YAML frontmatter block (--- ... ---)")
    raw, body = m.group(1), m.group(2)
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")

    slug = data.get("slug") or fallback_slug
    if not slug:
        raise ValueError("item has no 'slug' in frontmatter and no fallback")
    if "tier" not in data:
        raise ValueError(f"item {slug!r} has no 'tier' in frontmatter")
    if "title" not in data:
        raise ValueError(f"item {slug!r} has no 'title' in frontmatter")

    created = data.get("created")
    if isinstance(created, str):
        created = date.fromisoformat(created)
    elif created is not None and not isinstance(created, date):
        raise ValueError(f"item {slug!r} has a non-date 'created' value")

    return Item(
        slug=str(slug),
        tier=Tier.from_str(str(data["tier"])),
        title=str(data["title"]),
        body=body.strip(),
        tags=[str(t) for t in (data.get("tags") or [])],
        project=(str(data["project"]) if data.get("project") else None),
        created=created,
        links=[str(x) for x in (data.get("links") or [])],
    )
