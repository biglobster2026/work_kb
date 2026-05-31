"""work_kb — a file-based, three-tier knowledge base for AI agents.

The whole module is a *compiler*, not a server: you add markdown items, run
``kb build``, and it regenerates the navigation + agent-instruction files that
let any file-reading agent (VS Code Copilot, Claude, Cursor, …) consume the KB.
There is no daemon and no API — retrieval is delegated to the agent's own file
tools, which is exactly why it survives vendors reshuffling their agent layer.

Three tiers, each with a retrieval mechanism matched to its size:

* **foundation** (~100) — always relevant; enumerated inline in one INDEX so an
  agent loads the whole tier at once.
* **detail** (~10k) — pull on demand; a topic/tag *map* the agent navigates,
  then opens only the items it needs.
* **artifact** (~50k) — searchable archive; no enumeration at all, the agent
  greps the files (ripgrep handles 50k small files trivially).

See ``models.Tier`` for the contract and ``build`` for the pure compiler core.
"""

from __future__ import annotations

from work_kb.models import Item, Tier

__all__ = ["Item", "Tier"]
