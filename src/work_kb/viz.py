"""The knowledge-tree overview — a self-contained HTML page, generated at build.

A radial map of the KB whose geometry *is* the retrieval philosophy:

* **radial distance encodes frequency/tier** — foundation sits at the core
  (always loaded), detail forms the mid-ring (pulled on demand), artifacts are
  the outer leaves (the archive you search, not browse).
* **size encodes count/role** — cluster bubbles scale with how many items they
  hold; the root and tier hubs are fixed structural anchors.
* **color encodes attention/heat** — hotter (more populated) clusters glow more
  toward the brand orange; quiet ones stay pale.

It is a pure function (`render_overview_html`) so the layout is deterministic and
testable, and the output is a single file with inline CSS/JS and NO external
dependencies — it opens offline by double-click, which the files-only target box
requires. The artifact tier is rendered as count-sized cluster bubbles by
project, never as 50k individual nodes: the same non-enumeration discipline the
rest of the KB follows.
"""

from __future__ import annotations

import html
import json
import math
from collections import defaultdict
from dataclasses import dataclass

from work_kb.models import Item, Tier, shard

# Light-theme palette. Brand orange is the heat/attention hue; tiers are placed
# by radius, so color is free to mean "how populated" everywhere.
_ACCENT = "#E8650A"
_HEAT_LO = (243, 221, 196)  # pale peach — a near-empty cluster
_HEAT_HI = (232, 101, 10)  # deep brand orange — a hot cluster

# Canvas + ring radii. Foundation hugs the core; artifacts sit at the rim.
# Kept compact so the whole tree fits one screen without scrolling.
_W, _H = 900, 660
_CX, _CY = 450, 330
_R_FOUNDATION = 108
_R_DETAIL = 195
_R_ARTIFACT = 268


@dataclass
class _Node:
    kind: str  # root | hub | item | cluster
    label: str
    x: float
    y: float
    r: float
    fill: str
    tier: str = ""
    count: int = 0
    href: str = ""
    nid: str = ""


def _polar(angle_deg: float, radius: float) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return _CX + radius * math.cos(a), _CY + radius * math.sin(a)


def _heat(count: int, hi: int) -> str:
    """Interpolate pale→deep-orange by count, so density reads as warmth."""
    t = 0.0 if hi <= 0 else min(1.0, count / hi)
    # Gamma-bend so even small clusters show some warmth.
    t = t**0.6
    rgb = tuple(round(lo + (h - lo) * t) for lo, h in zip(_HEAT_LO, _HEAT_HI, strict=True))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _ring_angles(n: int, start: float = -90.0) -> list[float]:
    """n evenly-spaced angles around the circle, starting at the top."""
    if n <= 0:
        return []
    return [start + i * 360.0 / n for i in range(n)]


def _detail_clusters(items: list[Item]) -> list[tuple[str, list[Item]]]:
    by_tag: dict[str, list[Item]] = defaultdict(list)
    for it in items:
        for tag in it.tags or ["(untagged)"]:
            by_tag[tag].append(it)
    return sorted(by_tag.items(), key=lambda kv: (-len(kv[1]), kv[0]))


def _artifact_clusters(items: list[Item]) -> list[tuple[str, int]]:
    by_proj: dict[str, int] = defaultdict(int)
    for it in items:
        by_proj[it.project or "(no project)"] += 1
    return sorted(by_proj.items(), key=lambda kv: (-kv[1], kv[0]))


def _cluster_radius(count: int, hi: int) -> float:
    """Area ∝ count (sqrt of count for radius), clamped to a legible band."""
    base = math.sqrt(max(count, 1) / max(hi, 1))
    return 11.0 + base * 23.0


def _build_nodes(items: list[Item]) -> tuple[list[_Node], dict]:
    """Lay out every node and return them plus the JSON payload the side panel
    and search use. Pure geometry — no I/O."""
    by_tier: dict[Tier, list[Item]] = {t: [] for t in Tier}
    for it in items:
        by_tier[it.tier].append(it)
    for t in by_tier:
        by_tier[t].sort(key=lambda i: (i.title.lower(), i.slug))

    nodes: list[_Node] = [_Node("root", "Knowledge base", _CX, _CY, 30, "#3a3a3a", nid="root")]
    panel: dict[str, dict] = {}

    # --- Foundation: inner ring, one node per item (enumerated; it's small) ---
    fnd = by_tier[Tier.FOUNDATION]
    show_labels = len(fnd) <= 26
    for ang, it in zip(_ring_angles(len(fnd)), fnd, strict=True):
        x, y = _polar(ang, _R_FOUNDATION)
        nid = f"f:{it.slug}"
        href = f"00-foundation/items/{it.slug}.md"
        nodes.append(
            _Node(
                "item",
                it.title if show_labels else "",
                x,
                y,
                7,
                _ACCENT,
                tier="foundation",
                href=href,
                nid=nid,
            )
        )
        panel[nid] = {
            "kind": "foundation",
            "title": it.title,
            "href": href,
            "tags": it.tags,
        }

    # --- Detail: mid ring, one node per tag cluster (sized + heated by count) ---
    dclusters = _detail_clusters(by_tier[Tier.DETAIL])
    dhi = max((len(v) for _, v in dclusters), default=1)
    for ang, (tag, members) in zip(_ring_angles(len(dclusters), -90 + 7), dclusters, strict=True):
        x, y = _polar(ang, _R_DETAIL)
        nid = f"d:{tag}"
        nodes.append(
            _Node(
                "cluster",
                f"{tag} ({len(members)})",
                x,
                y,
                _cluster_radius(len(members), dhi),
                _heat(len(members), dhi),
                tier="detail",
                count=len(members),
                nid=nid,
            )
        )
        panel[nid] = {
            "kind": "detail",
            "title": tag,
            "count": len(members),
            "items": [
                {
                    "title": m.title,
                    "href": f"10-details/items/{shard(m.slug)}/{m.slug}.md",
                }
                for m in sorted(members, key=lambda m: m.title.lower())
            ],
        }

    # --- Artifacts: outer leaves, clustered by project, COUNTS ONLY ---
    aclusters = _artifact_clusters(by_tier[Tier.ARTIFACT])
    ahi = max((c for _, c in aclusters), default=1)
    for ang, (proj, count) in zip(_ring_angles(len(aclusters), -90 + 11), aclusters, strict=True):
        x, y = _polar(ang, _R_ARTIFACT)
        nid = f"a:{proj}"
        nodes.append(
            _Node(
                "cluster",
                f"{proj} ({count})",
                x,
                y,
                _cluster_radius(count, ahi),
                _heat(count, ahi),
                tier="artifact",
                count=count,
                nid=nid,
            )
        )
        panel[nid] = {
            "kind": "artifact",
            "title": proj,
            "count": count,
            "query": "" if proj.startswith("(") else f"project: {proj}",
        }

    counts = {t.value: len(by_tier[t]) for t in Tier}
    meta = {
        "panel": panel,
        "counts": counts,
        "tiers": {
            "foundation": _R_FOUNDATION,
            "detail": _R_DETAIL,
            "artifact": _R_ARTIFACT,
        },
    }
    return nodes, meta


def _svg(nodes: list[_Node]) -> str:
    parts: list[str] = [
        f'<svg id="tree" viewBox="0 0 {_W} {_H}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="Knowledge base radial overview">'
    ]
    # Tier guide rings, faintly, so the frequency gradient is legible.
    for r, lbl in (
        (_R_FOUNDATION, "core"),
        (_R_DETAIL, "branches"),
        (_R_ARTIFACT, "leaves"),
    ):
        parts.append(
            f'<circle cx="{_CX}" cy="{_CY}" r="{r}" class="ring"/>'
            f'<text x="{_CX}" y="{_CY - r - 6}" class="ringlbl">{lbl}</text>'
        )
    # Edges: root → every non-root node (drawn first, under the nodes).
    root = nodes[0]
    for n in nodes[1:]:
        parts.append(
            f'<line class="edge" x1="{root.x:.1f}" y1="{root.y:.1f}" '
            f'x2="{n.x:.1f}" y2="{n.y:.1f}"/>'
        )
    # Nodes + labels.
    for n in nodes:
        cls = f"node {n.kind}"
        href = html.escape(n.href, quote=True)
        title = html.escape(n.label or "")
        parts.append(
            f'<g class="{cls}" data-nid="{html.escape(n.nid, quote=True)}" '
            f'data-href="{href}" tabindex="0">'
            f'<circle cx="{n.x:.1f}" cy="{n.y:.1f}" r="{n.r:.1f}" '
            f'fill="{n.fill}"/>'
        )
        if n.kind == "root":
            parts.append(f'<text x="{n.x:.1f}" y="{n.y + 4:.1f}" class="rootlbl">KB</text>')
        elif n.label:
            dy = n.r + 13
            parts.append(f'<text x="{n.x:.1f}" y="{n.y + dy:.1f}" class="nlabel">{title}</text>')
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


def render_overview_html(items: list[Item]) -> str:
    """Pure: items -> a single self-contained HTML overview page."""
    nodes, meta = _build_nodes(items)
    svg = _svg(nodes)
    data_json = json.dumps(meta, ensure_ascii=False)
    c = meta["counts"]
    total = sum(c.values())

    return _TEMPLATE.format(
        accent=_ACCENT,
        svg=svg,
        data=data_json,
        n_found=c["foundation"],
        n_detail=c["detail"],
        n_artifact=c["artifact"],
        total=total,
    )


# Single-file template. Inline CSS/JS, no external requests.
_TEMPLATE = """<!DOCTYPE html>
<!-- GENERATED by `kb build` — do not edit by hand. -->
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Knowledge base — overview</title>
<style>
  :root {{
    --accent: {accent};
    --bg: #faf7f2; --panel: #fffdfa; --ink: #2b2b2b; --muted: #8a8074;
    --line: #ece4d8; --chip: #f3ece1;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink);
    font: 15px/1.5 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  header {{ padding: 18px 24px 10px; }}
  h1 {{ margin: 0 0 4px; font-size: 20px; font-weight: 650; }}
  .sub {{ color: var(--muted); font-size: 13px; }}
  .chips {{ display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }}
  .chip {{ background: var(--chip); border-radius: 999px; padding: 5px 13px;
    font-size: 13px; display: flex; gap: 7px; align-items: center; }}
  .chip b {{ font-weight: 650; }}
  .dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
  .layout {{ display: grid; grid-template-columns: 1fr 320px; gap: 8px;
    padding: 0 16px 20px; align-items: start; }}
  .stage {{ position: relative; background:
    radial-gradient(circle at 50% 52%, #fffefb 0%, var(--bg) 78%);
    border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }}
  svg {{ width: 100%; height: auto; max-height: 78vh; display: block;
    margin: 0 auto; }}
  .ring {{ fill: none; stroke: #efe7db; stroke-dasharray: 3 6; }}
  .ringlbl {{ fill: #c9bba6; font-size: 11px; text-anchor: middle;
    letter-spacing: .12em; text-transform: uppercase; }}
  .edge {{ stroke: var(--line); stroke-width: 1; }}
  .node circle {{ cursor: pointer; transition: r .12s ease, filter .12s ease; }}
  .node:hover circle, .node:focus circle {{ filter: brightness(1.05)
    drop-shadow(0 1px 4px rgba(232,101,10,.45)); outline: none; }}
  .node.cluster circle {{ stroke: #fff; stroke-width: 1.5; }}
  .rootlbl {{ fill: #fff; font-size: 12px; font-weight: 700; text-anchor: middle; }}
  .nlabel {{ fill: #5c5346; font-size: 11px; text-anchor: middle;
    pointer-events: none; }}
  .node.dim {{ opacity: .18; }}
  .node.hit circle {{ stroke: var(--accent); stroke-width: 3; }}
  aside {{ background: var(--panel); border: 1px solid var(--line);
    border-radius: 14px; padding: 16px; position: sticky; top: 12px; }}
  .search {{ width: 100%; padding: 8px 11px; border: 1px solid var(--line);
    border-radius: 9px; font-size: 14px; background: #fff; color: var(--ink); }}
  .legend {{ margin: 14px 0 6px; font-size: 12px; color: var(--muted); }}
  .legend div {{ margin: 3px 0; display: flex; gap: 8px; align-items: center; }}
  #panel {{ margin-top: 14px; }}
  #panel h2 {{ font-size: 15px; margin: 0 0 2px; }}
  #panel .tier-tag {{ font-size: 11px; text-transform: uppercase;
    letter-spacing: .08em; color: var(--muted); }}
  #panel ul {{ list-style: none; padding: 0; margin: 10px 0 0;
    max-height: 340px; overflow: auto; }}
  #panel li {{ padding: 5px 0; border-bottom: 1px solid var(--line); }}
  #panel a {{ color: var(--accent); text-decoration: none; }}
  #panel a:hover {{ text-decoration: underline; }}
  .hint {{ color: var(--muted); font-size: 13px; }}
  code {{ background: var(--chip); padding: 1px 6px; border-radius: 5px;
    font-size: 12px; }}
  #tip {{ position: fixed; pointer-events: none; background: #2b2b2b;
    color: #fff; padding: 5px 9px; border-radius: 7px; font-size: 12px;
    opacity: 0; transition: opacity .1s; white-space: nowrap; z-index: 9; }}
</style>
</head>
<body>
<header>
  <h1>Knowledge base — overview</h1>
  <div class="sub">A knowledge tree: distance from the core encodes how often
    a tier is consulted. Core facts sit at the center; the archive forms the
    outer leaves.</div>
  <div class="chips">
    <span class="chip"><span class="dot" style="background:var(--accent)"></span>
      Foundation <b>{n_found}</b></span>
    <span class="chip"><span class="dot" style="background:#e9923f"></span>
      Details <b>{n_detail}</b></span>
    <span class="chip"><span class="dot" style="background:#d9c3a3"></span>
      Artifacts <b>{n_artifact}</b></span>
    <span class="chip">Total <b>{total}</b></span>
  </div>
</header>
<div class="layout">
  <div class="stage">{svg}</div>
  <aside>
    <input id="search" class="search" list="kb-search" placeholder="Jump to a fact or topic…" autocomplete="off"/>
    <datalist id="kb-search"></datalist>
    <div class="legend">
      <div><span class="dot" style="background:var(--accent)"></span>
        ring 1 · core facts (always loaded)</div>
      <div><span class="dot" style="background:#e9923f"></span>
        ring 2 · topic branches (on demand)</div>
      <div><span class="dot" style="background:#d9c3a3"></span>
        ring 3 · archive leaves (searched)</div>
      <div style="margin-top:6px">bubble size & warmth = item count</div>
    </div>
    <div id="panel">
      <p class="hint">Hover a node for its name. Click a topic or archive
        cluster to see what's inside; click a core fact to open it.</p>
    </div>
  </aside>
</div>
<div id="tip"></div>
<script id="kb-data" type="application/json">{data}</script>
<script>
(function() {{
  const META = JSON.parse(document.getElementById("kb-data").textContent);
  const panel = META.panel;
  const tip = document.getElementById("tip");
  const panelEl = document.getElementById("panel");
  const nodes = Array.from(document.querySelectorAll(".node"));

  // Search dropdown: foundation facts + topic/archive clusters (NOT 50k leaves).
  const dl = document.getElementById("kb-search");
  const opts = [];
  for (const [nid, p] of Object.entries(panel)) {{
    if (p.kind === "artifact" && p.title.startsWith("(")) continue;
    opts.push({{nid, label: p.title}});
  }}
  opts.sort((a, b) => a.label.localeCompare(b.label));
  for (const o of opts) {{
    const el = document.createElement("option");
    el.value = o.label; el.dataset.nid = o.nid; dl.appendChild(el);
  }}

  function esc(s) {{ const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }}

  function showPanel(nid) {{
    const p = panel[nid];
    if (!p) return;
    let html = `<span class="tier-tag">${{esc(p.kind)}}</span><h2>${{esc(p.title)}}</h2>`;
    if (p.kind === "foundation") {{
      html += `<p class="hint">Core fact${{p.tags && p.tags.length ? " · " + p.tags.map(esc).join(", ") : ""}}</p>`;
      html += `<p><a href="${{esc(p.href)}}">Open item →</a></p>`;
    }} else if (p.kind === "detail") {{
      html += `<p class="hint">${{p.count}} item${{p.count===1?"":"s"}} under this topic.</p><ul>`;
      for (const it of p.items) html += `<li><a href="${{esc(it.href)}}">${{esc(it.title)}}</a></li>`;
      html += `</ul>`;
    }} else {{
      html += `<p class="hint">${{p.count}} archived item${{p.count===1?"":"s"}}. The archive is not listed — search it:</p>`;
      html += p.query ? `<p><code>${{esc(p.query)}}</code> in <code>kb/20-artifacts/items/</code></p>`
                      : `<p class="hint">Search <code>kb/20-artifacts/items/</code> by keyword.</p>`;
    }}
    panelEl.innerHTML = html;
  }}

  function highlight(nid) {{
    nodes.forEach(n => {{
      n.classList.toggle("hit", n.dataset.nid === nid);
      n.classList.toggle("dim", nid && n.dataset.nid !== nid && n.dataset.nid !== "root");
    }});
  }}
  function clearHi() {{ nodes.forEach(n => n.classList.remove("hit", "dim")); }}

  nodes.forEach(n => {{
    const nid = n.dataset.nid;
    n.addEventListener("mousemove", e => {{
      const p = panel[nid];
      const label = p ? p.title + (p.count ? ` · ${{p.count}}` : "") : (nid === "root" ? "Knowledge base" : "");
      if (!label) return;
      tip.textContent = label; tip.style.opacity = 1;
      tip.style.left = (e.clientX + 12) + "px"; tip.style.top = (e.clientY + 12) + "px";
    }});
    n.addEventListener("mouseleave", () => tip.style.opacity = 0);
    function activate() {{
      const p = panel[nid];
      if (p && p.kind === "foundation" && n.dataset.href) {{ location.href = n.dataset.href; return; }}
      showPanel(nid); highlight(nid);
    }}
    n.addEventListener("click", activate);
    n.addEventListener("keydown", e => {{ if (e.key === "Enter") activate(); }});
  }});

  document.getElementById("search").addEventListener("change", e => {{
    const opt = Array.from(dl.options).find(o => o.value === e.target.value);
    if (opt) {{ showPanel(opt.dataset.nid); highlight(opt.dataset.nid); }}
    else clearHi();
  }});
}})();
</script>
</body>
</html>
"""
