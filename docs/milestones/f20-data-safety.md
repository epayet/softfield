# Milestone F20: data safety

> **Status: planned** (2026-10-07, with the owner, in a terminal session). **State:** ready · **Priority:** 1 · **Area:** factory
> The owner (2026-10-07): "does the database ever get backed up, or committed to git? I'm concerned about losing data." It doesn't: `~/.local/share/software-factory/factory-metrics.sqlite` is outside the repo (ADR 13 item 1), and its only copy is a one-off from 2026-10-02.

## Outcome
- Once a day, the runner copies the metrics database into a Dropbox folder, keeping the last 14 copies. It keeps working if the copy fails, and says so.
- Approving a card's plan also commits its planning thread to `docs/planning/`, so the conversation behind a decision is in git with it.

## What is only in the database
Planning threads (the owner's messages, the lead's points and proposals), the owner's requests and desk items, and the agents' ratings (routing). Runs, jobs and tokens come partly back with `runner backfill`, but from `var/runs/`, which is not in git either.

## Decisions
- **D1 Backup** (ADR 13 item 1, amended 2026-10-07): `workflow/runner.toml` gets
  ```toml
  [backup]
  dir = "~/Dropbox/software-factory-backups"
  keep = 14
  every_hours = 24
  ```
  - A copy is `factory-metrics-<YYYYMMDD-HHMM>.sqlite`, written with SQLite's online backup (`sqlite3.Connection.backup`) to a temporary name in `dir`, then renamed: Dropbox only ever sees a finished file. Never the live database in Dropbox.
  - It is due when the newest copy in `dir` is older than `every_hours`, or there is none. The runner checks at its start, at each pick, and while it waits (for Claude, for the owner's pause, or with nothing to do), since it may run for weeks without a restart.
  - `dir` is created if missing. A copy that fails (no space, `dir` not writable) is a note in the session report and a console line, never an error that stops the run; the next check tries again.
  - Past `keep`, the oldest copies in `dir` matching the name pattern are removed; nothing else in `dir` is touched.
- **D2 Thread export** (ADR 20 item 7, amended 2026-10-07): `_approve_plan` (`runner/requests.py`) writes `docs/planning/<card's full key>.md` in the same commit as the drafts: a title, then every message oldest first, each with its author ("The owner" / "The lead") and time, the lead's points numbered with title, answer and action, the owner's comments by point, and each proposal's title and kind. A later approval on the same thread rewrites the file with the whole thread. The general thread has no card, so its approved merges export nothing.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | metrics-backup | L | 5 | – | D1: the `[backup]` config, the copy and its pruning, checked at start, at each pick and while waiting |
| 02 | thread-export | L | 4 | – | D2: approving a plan commits its thread to `docs/planning/` |

Both touch `runner/` (protected): lead tickets.
