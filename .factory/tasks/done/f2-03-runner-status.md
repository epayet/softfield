---
id: f2-03-runner-status
milestone: f2
depends_on: [f2-02-claude-window]
agent: lead
difficulty: 5
files:
  - runner/loop.py
  - runner/metrics.py
  - runner/cli.py
  - factory_dashboard/templates/_partials/running.html
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_metrics.py
  - tests/runner/test_cli.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
While the runner is alive, the dashboard always says what it's doing and which ticket a wait is for, and a Ctrl-C leaves no run looking alive or "on the reserve".

### Context
Read `docs/milestones/f1.md` D3 (amended 2026-10-02) and `docs/reviews/factory-f1.md` finding 4, then `runner/loop.py` (`doing`, `record_start`, `WAITING_FOR_CLAUDE`, `_wait_for_reset`, `at_reserve`, `_next_task`), `runner/metrics.py` (`set_run_reserve`, `close_abandoned`, the `runs` columns `activity`, `waiting_until`, `reserve`), `runner/cli.py` (the `milestone` command and its self-restart) and `factory_dashboard/templates/_partials/running.html`. Test-first.
- **Seen by the owner:** between two tickets the page said a bare "Running" (`record_start` clears `activity`, and nothing sets it until the next job, gates or warm-up); "waiting for Claude" between jobs (`_wait_for_reset`) names no ticket; after Ctrl-C, run `20261002-055804` kept `ended = NULL` and `reserve = 1`, so "on Claude's reserve" stayed until the heartbeat went stale.
- **Activity between tickets:** "picking the next ticket", "asking you about Claude's reserve" (and the 5-hour question from f2-02), "waiting for Claude · <ticket> until HH:MM" (the parked ticket that resumes first), "restarting after a runner change".
- **Ctrl-C and crashes:** on `KeyboardInterrupt` (and on any exit of the command), the run's `ended` is set, `activity` and `waiting_until` cleared, `reserve` set to 0. A self-restart after a runner change keeps the yes, as now (ADR 15 item 5), on the new run.
- `factory_dashboard/templates/_partials/running.html` shows the activity text whole when no job runs.

### Done when
- between two tickets in a test run, the run's `activity` is never empty while it lives
- a wait for a reset names the ticket it waits for, in `activity` and on the Overview
- after a simulated Ctrl-C the run has `ended` set and `reserve` 0, and the Overview says nothing is running
- `uv run runner check-all --task f2-03-runner-status` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
