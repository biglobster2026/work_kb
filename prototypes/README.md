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

Sample history is seeded for past days so the patterns are visible; ticks are
stored in `localStorage` for the current browser only. Task definitions live in
the `DAILY` / `WEEKLY` / `MONTHLY` arrays at the top of the `<script>` block.
