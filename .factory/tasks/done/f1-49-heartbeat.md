---
id: f1-49-heartbeat
milestone: f1
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/loop.py
  - runner/metrics.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A runner that is alive keeps its run's heartbeat under 30 s old, whatever it is doing, so the dashboard stops reporting a live runner as stopped.

### Context
Read `runner/loop.py` (`with_progress`, `_start_run`, `_finish_run`, `live_update`, `call_claude`), `runner/metrics.py` (`open_db`, `update_run_heartbeat`), and the stale check in `factory_dashboard/overview.py` (`LIVE`, `needs_you`). Test-first.
- **What happened (2026-10-01):** during f1-18-probes the Overview said "The runner's heartbeat stopped 3 min ago mid-job: a crash or a closed terminal" while the runner was fine and its lead job was running `check-all`. The owner stopped a healthy runner.
- **Why:** only OpenCode attempts beat while they run (`live_update`, every `LIVE_EVERY` from `runner/local_model.py`). A Claude job (`run_claude` waits on a blocking `subprocess.run`), the gates and `check-all` after a job, and the `time.sleep` of a usage-limit or transient pause in `call_claude` write nothing until they end. Anything longer than the dashboard's 2-minute `LIVE` looks dead.
- **The fix:** a heartbeat that means "the runner's process is alive". A daemon thread, started once the run's row exists in `_start_run` and stopped in `_finish_run` before the connection closes, writes the run's heartbeat every `LIVE_EVERY` seconds. **sqlite3 connections can't cross threads:** the thread opens its own connection to `s.cfg.metrics_db`. It is best effort, like `_record`: a failed write is noted once (`_metrics_failed`) and never stops the run. A daemon thread dies with the process, so a crash or Ctrl-C still leaves a stale heartbeat, as D3 wants.
- Keep the existing beats at job start and end; the dashboard's 2-minute `LIVE` doesn't change.

### Done when
- while a fake `run_claude` blocks for longer than the beat interval (shortened in the test), the run's heartbeat advances at least twice
- the heartbeat also advances during a usage-limit pause in `call_claude`
- after `_finish_run`, the thread has stopped: no beat lands after the run's `ended`
- a metrics database that fails mid-run (the thread's write raises) leaves one note in the session report and the run goes on
- a session opened with no command (`open_session(cfg, None)`) starts no thread

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
