# work_kb

A file-based, three-tier knowledge base that **any file-reading AI agent**
(VS Code Copilot, Claude, Cursor, …) can consume — no service, no API, no admin.

It is a *compiler*, not a server: you add markdown items and run `kb build`,
which regenerates the navigation and agent-instruction files. Retrieval is
delegated to the agent's own file tools, so it survives vendors reshuffling
their agent layer.

## The three tiers

| Tier | Size | Role | How an agent retrieves it |
|------|------|------|---------------------------|
| **foundation** | ~100 | always-relevant core facts | reads `kb/00-foundation/INDEX.md` whole |
| **detail** | ~10k | pull on demand | navigates `kb/10-details/INDEX.md` (a topic map) → opens items |
| **artifact** | ~50k | searchable archive of notes/snippets | **greps** `kb/20-artifacts/items/` |

The mechanism matches the size: foundation *enumerates*, details *navigate*,
artifacts *search*. A 10k-line flat index would defeat itself, so each tier
gets only the structure it can afford.

## The integration surface

`kb build` emits an instruction file for every major coding-agent convention
from a **single canonical protocol** (so they never drift), plus a
machine-readable catalog. Nothing else to wire up — drop the repo in and the
agent picks it up.

| File | Agent / convention |
|------|--------------------|
| `.github/copilot-instructions.md` | GitHub Copilot, repo-wide (auto-applied) |
| `.github/instructions/knowledge-base.instructions.md` | GitHub Copilot, path-scoped (`applyTo: "**"` frontmatter) |
| `AGENTS.md` | OpenAI Codex + the agents.md ecosystem (Cursor, Windsurf, Jules, Factory, Amp, Devin…) |
| `CLAUDE.md` | Claude Code |
| `.cursor/rules/knowledge-base.mdc` | Cursor project rule (MDC, `alwaysApply`) |
| `kb/index.json` | Machine-readable catalog for tools/programs |
| `kb/overview.html` | Human knowledge-tree overview (open in a browser) |

Adding or fixing a convention is a one-line entry in `agentfiles.TARGETS` — these
formats change often, so the registry is built to absorb that. `kb/index.json`
carries a `schema_version` and describes each tier's retrieval mode, item paths,
and topic/project clusters, so a program can consume the KB without parsing
markdown (artifacts stay clustered-by-count, never enumerated).

## Usage

```bash
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"

kb add --tier foundation --title "Project mission"
kb add --tier detail --title "Auth retry uses jitter" --tags auth,reliability
cat notes.txt | kb add --tier artifact --title "Standup 2026-05-31" --body -

kb build           # regenerate all navigation + agent-instruction files
kb validate        # dup slugs, dangling links, soft-cap pressure
kb stats           # counts per tier
kb promote auth-retry-uses-jitter --to foundation
kb pack "auth retry"   # assemble one CONTEXT.md for browse-less agents
```

## Design notes

- **Deterministic substrate.** Every core module (`models`, `build`,
  `validate`, `recall`, `viz`, `agentfiles`, `index`) is a pure function — no
  I/O, no LLM. `store` is the only thing that touches disk; `cli` is a thin
  shell. The tests assert real behavior, not tautologies.
- **One protocol, many formats.** The agent instruction files all render from a
  single canonical body in `agentfiles.py`, so Copilot / Codex / Claude / Cursor
  never see divergent guidance. The vendor formats change often; the registry
  makes each change a one-liner.
- **Soft caps, not hard limits.** `validate` *warns* as a tier fills. The
  foundation cap is load-bearing: tier 1 must stay small enough to dump into an
  agent's context wholesale.
- **Sharding.** Detail and artifact items spread across 256 (`items/<hex>/`)
  buckets so 50k files don't choke git or the filesystem.
- **No search engine here.** At KB scale the agent's own ripgrep is the right
  tool. If artifact full-text recall ever needs sub-millisecond ranking at
  scale, that's where a Tantivy index would slot in — deliberately not built
  until the need is real.
