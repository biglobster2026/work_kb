"""Integrity checks — pure: items in, a list of findings out.

Catches the things that silently degrade a file-based KB: duplicate slugs (two
files claiming the same identity), dangling cross-references, and tiers drifting
past their soft cap (the foundation cap is the one that matters — tier 1 must
stay small enough to load wholesale)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from work_kb.models import SOFT_CAPS, Item, Tier


class Level(StrEnum):
    ERROR = "error"
    WARN = "warn"


@dataclass(frozen=True)
class Finding:
    level: Level
    message: str


def validate(items: list[Item]) -> list[Finding]:
    findings: list[Finding] = []

    # Duplicate slugs — slugs are identities; collisions break links and writes.
    counts = Counter(it.slug for it in items)
    for slug, n in sorted(counts.items()):
        if n > 1:
            findings.append(Finding(Level.ERROR, f"duplicate slug {slug!r} ({n} files)"))

    # Dangling links — a cross-reference to a slug that doesn't exist.
    known = set(counts)
    for it in items:
        for target in it.links:
            if target not in known:
                findings.append(
                    Finding(Level.ERROR, f"{it.slug!r} links to unknown slug {target!r}")
                )

    # Soft-cap pressure — warn (don't block) as a tier fills. Foundation first.
    per_tier = Counter(it.tier for it in items)
    for tier in Tier:
        cap = SOFT_CAPS[tier]
        if cap and per_tier[tier] > cap * 0.9:
            findings.append(
                Finding(
                    Level.WARN,
                    f"tier {tier.value!r} has {per_tier[tier]} items, "
                    f"near/over its soft cap of {cap}"
                    + (" — keep it dump-able into context" if tier is Tier.FOUNDATION else ""),
                )
            )

    return findings
