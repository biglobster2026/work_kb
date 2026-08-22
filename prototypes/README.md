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

### Sharing it from OneDrive / SharePoint — one writer, many readers

Put `cadence-board.html` and `state.js` side by side in the shared folder. The
dashboard loads `state.js` on open, so everyone sees the same record without a
server.

- **Readers** open the file and see whatever was last published. They can tick
  things, but those marks stay in their own browser and change nothing for
  anyone else.
- **The owner** ticks as normal, then presses **Publish record…**, copies the
  generated text over `state.js`, and lets OneDrive sync. The status bar counts
  unpublished changes so it is obvious when the shared copy is behind.

The sample history is never published — the first `state.js` starts from real
marks only. Sample data also switches itself off automatically as soon as a
`state.js` is present, so nobody sees invented history beside the real record.

This is deliberately single-writer. Two people publishing independently would
each overwrite a whole-document snapshot and silently drop the other's marks; a
file on a sync service cannot merge concurrent edits. If everyone needs to tick
a genuinely shared board, use a SharePoint list, an Excel workbook (co-authoring
handles the merge), or a hosted page with a backend.

Note that a `.json` or `.csv` sidecar will *not* work in place of `state.js`:
`fetch()` and `XMLHttpRequest` are blocked on `file://` origins, while a
`<script src>` is not. That is why the record is a `.js` file assigning
`window.CADENCE_STATE`.

Also check how your tenant serves `.html` from SharePoint — the default strict
browser file handling downloads HTML rather than rendering it. Opening through
the synced OneDrive folder avoids this.

### Running it without a shared record

Set `SHOW_SAMPLE_WHEN_EMPTY = false` at the top of the script for a board that
starts completely empty. While it is `true` and no `state.js` exists, past days
are pre-filled with fabricated history so the patterns are visible in a demo.

### What travels with the file, and what doesn't

Ticks are written to `localStorage`, not to the file — a page cannot write to
its own file on disk, which is why publishing is a copy-paste step rather than
a save. So the `.html` itself is byte-identical before and after you use it and
carries none of your marks; everything shared travels in `state.js`.

Storage is per browser and per profile: a private window starts empty, and
clearing site data wipes it. Reads and writes are wrapped in `try`/`catch`, so
a browser that blocks storage on `file://` degrades to in-memory — ticks work
for the session and reset on reload — rather than breaking the page.

The one external request is the Google Fonts stylesheet; with no network the
page falls back to system fonts and is otherwise unaffected.
