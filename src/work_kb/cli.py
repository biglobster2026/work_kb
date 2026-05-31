"""The `kb` command — a thin shell over the pure modules.

kb add --tier detail --title "..." [--tags a,b] [--project p] [body via -]
kb build                 regenerate all navigation + agent-instruction files
kb promote <slug> --to foundation     (and the inverse: demote)
kb validate              report integrity findings; nonzero exit on errors
kb stats                 item counts per tier
kb pack "<query>"        assemble a single CONTEXT.md for browse-less agents
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from work_kb.build import build
from work_kb.models import Item, Tier, slugify
from work_kb.recall import rank
from work_kb.store import Store
from work_kb.validate import Level, validate


def _store(args: argparse.Namespace) -> Store:
    return Store(args.root)


def cmd_add(args: argparse.Namespace) -> int:
    store = _store(args)
    body = ""
    if args.body == "-":
        body = sys.stdin.read()
    elif args.body:
        body = args.body
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    item = Item(
        slug=args.slug or slugify(args.title),
        tier=Tier.from_str(args.tier),
        title=args.title,
        body=body,
        tags=tags,
        project=args.project,
        created=date.today(),
    )
    if store.find(item.slug):
        print(f"error: slug {item.slug!r} already exists", file=sys.stderr)
        return 1
    path = store.write_item(item)
    print(f"added {item.slug} -> {path.relative_to(store.root)}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    store = _store(args)
    files = build(store.read_all())
    written = store.write_generated(files)
    print(f"built {len(written)} files")
    for p in written:
        print(f"  {p.relative_to(store.root)}")
    return 0


def _retier(args: argparse.Namespace, new_tier: Tier) -> int:
    store = _store(args)
    found = store.find(args.slug)
    if not found:
        print(f"error: no item with slug {args.slug!r}", file=sys.stderr)
        return 1
    item, _ = found
    path = store.move_item(item, new_tier)
    print(f"moved {item.slug} -> {new_tier.value} ({path.relative_to(store.root)})")
    print("run `kb build` to refresh navigation")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    return _retier(args, Tier.from_str(args.to))


def cmd_demote(args: argparse.Namespace) -> int:
    return _retier(args, Tier.from_str(args.to))


def cmd_validate(args: argparse.Namespace) -> int:
    store = _store(args)
    findings = validate(store.read_all())
    if not findings:
        print("ok: no issues")
        return 0
    errors = 0
    for f in findings:
        print(f"{f.level.value.upper()}: {f.message}")
        if f.level is Level.ERROR:
            errors += 1
    return 1 if errors else 0


def cmd_stats(args: argparse.Namespace) -> int:
    store = _store(args)
    items = store.read_all()
    per_tier = {t: 0 for t in Tier}
    for it in items:
        per_tier[it.tier] += 1
    print(f"{len(items)} items total")
    for t in Tier:
        print(f"  {t.value:<11} {per_tier[t]}")
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    store = _store(args)
    hits = rank(args.query, store.read_all(), limit=args.limit)
    out = [f"# Context for: {args.query}", ""]
    for h in hits:
        if h.score <= 0:
            continue
        out.append(f"## {h.item.title}  ({h.item.tier.value})")
        if h.item.body:
            out.append(h.item.body)
        out.append("")
    content = "\n".join(out) + "\n"
    dest = Path(args.out)
    dest.write_text(content, encoding="utf-8")
    print(f"packed {len([h for h in hits if h.score > 0])} items -> {dest}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kb", description="File-based three-tier knowledge base.")
    p.add_argument("--root", default=".", help="repo root (default: cwd)")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="add an item")
    a.add_argument("--tier", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--slug", default=None)
    a.add_argument("--tags", default=None, help="comma-separated")
    a.add_argument("--project", default=None)
    a.add_argument("--body", default=None, help="body text, or '-' to read stdin")
    a.set_defaults(func=cmd_add)

    b = sub.add_parser("build", help="regenerate navigation + agent files")
    b.set_defaults(func=cmd_build)

    pr = sub.add_parser("promote", help="move an item to a higher tier")
    pr.add_argument("slug")
    pr.add_argument("--to", required=True)
    pr.set_defaults(func=cmd_promote)

    dm = sub.add_parser("demote", help="move an item to a lower tier")
    dm.add_argument("slug")
    dm.add_argument("--to", required=True)
    dm.set_defaults(func=cmd_demote)

    v = sub.add_parser("validate", help="check integrity")
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("stats", help="item counts per tier")
    s.set_defaults(func=cmd_stats)

    pk = sub.add_parser("pack", help="assemble a single CONTEXT.md for a query")
    pk.add_argument("query")
    pk.add_argument("--out", default="CONTEXT.md")
    pk.add_argument("--limit", type=int, default=10)
    pk.set_defaults(func=cmd_pack)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
