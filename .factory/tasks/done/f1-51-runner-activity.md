---
id: f1-51-runner-activity
milestone: f1
depends_on: []
agent: lead
difficulty: 7
files:
  - runner/metrics.py
  - runner/loop.py
  - runner/claude.py
  - runner/owner.py
  - runner/console.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_loop.py
  - tests/runner/test_claude.py
  - tests/runner/test_owner.py
  - tests/runner/test_console.py
---

### Goal
The metrics database always says what the runner is doing, including Claude's live tokens and its waits, and the owner's items clear as soon as the owner has acted on them.

### Context
Read `docs/milestones/f1.md` (D3 and D8, each "Amended 2026-10-02", and the Replan log's 2026-10-02 entry), `runner/metrics.py` (`MIGRATIONS`, `upsert_run`, `update_run_heartbeat`, `upsert_ticket`), `runner/loop.py` (`_start_run`, `sync_tickets`, `record_ticket`, `call_claude`, `_park`, `at_reserve`, `_check_all`, `live_update`), `runner/claude.py` (`run_claude`, `_parse_stream`), `runner/local_model.py` (`run_streaming`, `run_opencode`: the live pattern to follow), `runner/owner.py` (`_RERUN_KINDS`, `_record_items`, `_resolve`) and `runner/console.py` (`first_line`, `summary`). Test-first.
- **Seen by the owner on 2026-10-01:** Running now said "running" while the runner slept on a Claude limit; Claude jobs showed "elapsed time only"; gates, `check-all` and the warm-up showed nothing; Needs-you kept "waits for Claude's reserve … answer y" after the owner answered y, and "tickets paused behind …" after the rerun (items resolve only at the next verdict, and runs restarted before reaching one); `↳` lines were cut at `SUMMARY_CHARS`.
- **Schema (a new migration, `PRAGMA user_version` 3):** `runs` gains `activity TEXT`, `waiting_until TEXT` and `reserve INTEGER`. A function sets them; `waiting_until` is cleared when the wait ends, `activity` when a job starts.
- **Where activity is written:** gates (`"gates · <ticket>"`), `check-all` (`"check-all on main"` or `"check-all · <ticket>"`), the local model's warm-up (`"warm-up"`), every pause for a limit or a passing error (`"waiting for Claude"` with `waiting_until`), and the idle wait when nothing can run without Claude. Best effort, like `_record`.
- **Claude live:** `run_claude` reads its stream-json line by line as it arrives (like `run_streaming`), and every `LIVE_EVERY` seconds hands the tokens and turns so far to the loop, which writes them as `live_update` does for OpenCode. The final result and the limit handling stay as they are.
- **Owner items:** at session start, `runner milestone <key>` resolves that milestone's open items of the kinds in `_RERUN_KINDS` (the rerun is what they asked for); the closing verdict reopens what still applies, as now. A yes to the reserve question resolves that ticket's `reserve` item at once and sets the run's `reserve`.
- **The queue:** `sync_tickets` also marks `ready` rows whose file no longer exists in `tasks/` (the DB still lists `f1-30-allowance-forecast`, deleted by ADR 15) with a state that isn't `ready` (`removed`).
- **Check, and fix if wrong:** f1-22's parked `resets_at` in `var/runs/state.json` said 23:00 while Claude's refusal said 01:40 (`_park`). A parked job's reset should be the refusal's.
- `console.summary` prints the whole first line, uncut.

### Done when
- a run waiting on a Claude limit has `waiting_until` set and `activity` "waiting for Claude"; both clear when the wait ends
- during gates, `check-all` and the warm-up, the run's `activity` names them
- a Claude job's row shows tokens and steps before it ends (a fake stream in the test)
- after a rerun's session start, the milestone's earlier `reserve`, `escalated`, `blocked` and `review-stop` items are resolved; a yes to the reserve resolves its item and sets `runs.reserve`
- a ready ticket whose file was deleted is no longer `ready` after `sync_tickets`
- a 300-character summary prints whole
- an existing database migrates to version 3 and keeps its rows
- `uv run runner check-all --task f1-51-runner-activity` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
