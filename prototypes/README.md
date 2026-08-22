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

### Before you share the file

Set `SEED_SAMPLE_HISTORY = false` at the top of the script. While it is `true`,
past days are pre-filled with fabricated history so the patterns are visible in
a demo — anyone you send the file to would open it and see a record that looks
real but isn't, anchored to *their* today rather than yours.

### What travels with the file, and what doesn't

Ticks are written to `localStorage`, not to the file — a page cannot write to
its own file on disk. So the `.html` you attach to an email is byte-identical
before and after you use it, and it carries none of your marks. Each recipient
gets a private board of their own; nothing syncs between them, and nobody sees
anyone else's ticks. A shared board would need a server.

Storage is per browser and per profile: a private window starts empty, and
clearing site data wipes it. Reads and writes are wrapped in `try`/`catch`, so
a browser that blocks storage on `file://` degrades to in-memory — ticks work
for the session and reset on reload — rather than breaking the page.

The one external request is the Google Fonts stylesheet; with no network the
page falls back to system fonts and is otherwise unaffected.
