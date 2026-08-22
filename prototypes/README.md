# Prototypes

## `cadence-board.html`

A recurring-task tracker in calendar form. Open the file in a browser — it is
self-contained (one HTML file, no build step, no dependencies).

The organising rule: **a task's name appears at its own frequency, never more
often than that.**

- **Daily** tasks are never written into day cells. In the month grid each day
  carries a five-segment bar — one segment per daily habit, filled when kept —
  so a day reads as rhythm rather than as five repeated lines of text.
- **Weekly** tasks appear once a week, as a pill on their own weekday.
- **Monthly** tasks appear once a month, as a pill on their own date.
- The **ledger** underneath is the full record: one row per task (named exactly
  once), one column per day. Dailies fill every column; weeklies get one square
  per week; monthlies get one square per month. Streaks sit at the end of each
  row.
- The **focus rail** on the right is the only place a task's full name and its
  checkbox appear together — for the selected day.
- A `names` / `dots` toggle collapses the dated pills to coloured dots when even
  a weekly label feels like too much ink.

Task definitions live in the `DAILY` / `WEEKLY` / `MONTHLY` arrays at the top of
the `<script>` block.

### Two modes, one file

The board decides which mode it is in from a single baked constant at the top
of the file, `window.CADENCE_SNAPSHOT.published`.

**Working copy** (`published: null`) — your live board. Everything you tick is
persisted to `localStorage` immediately; nothing else is needed to use it.

**Snapshot** (`published` set) — what the team consumes. Publishing serialises
this page with the current marks baked in as a constant, so the snapshot is one
self-contained HTML file with no sidecar and no server. It opens read-only:
ticking does nothing, the publish and clear controls are hidden, and the status
bar says what it is and when it was taken.

### Publishing

Press **Publish snapshot…**. Chrome and Edge open a native save dialog, so you
can save straight into the synced OneDrive folder — the File System Access API
is permitted on a `file://` origin, which was verified rather than assumed.
Other browsers fall back to a normal download that you then move into place.

The snapshot is built by cloning the live document, emptying every container
that `render()` writes into, and replacing the baked constant. It therefore
ships the application rather than a frozen rendering of it, and rebuilds itself
on open like any other copy.

Sample history is never baked into a snapshot. While it is showing, the status
bar says so, because otherwise a full-looking working copy would publish an
almost empty board.

### Running it without sample history

Set `SHOW_SAMPLE_WHEN_EMPTY = false` at the top of the script for a working copy
that starts completely empty.

### What travels with the file, and what doesn't

Ticks are written to `localStorage`, not into the file — a page cannot modify
its own file on disk. Your working copy is therefore byte-identical before and
after you use it, and carries none of your marks; publishing writes a *separate*
file with the marks baked in.

Storage is per browser and per profile, so keep the working copy on one machine:
a private window starts empty, and clearing site data wipes it. Publish
regularly — the snapshot in the shared folder doubles as your backup. Reads and writes are wrapped in `try`/`catch`, so
a browser that blocks storage on `file://` degrades to in-memory — ticks work
for the session and reset on reload — rather than breaking the page.

The one external request is the Google Fonts stylesheet; with no network the
page falls back to system fonts and is otherwise unaffected.
