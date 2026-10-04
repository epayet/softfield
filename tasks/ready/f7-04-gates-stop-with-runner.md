---
id: f7-04-gates-stop-with-runner
milestone: f7-factory-fixes
depends_on: []
agent: lead
difficulty: 3
files:
  - runner/procs.py
tests:
  - tests/runner/test_procs.py
---

### Goal
When the runner stops (Ctrl-C, a signal, an error), the gate or check it was running stops with it.

### Context
Read `run_bounded` in `runner/procs.py`. Test-first.
- It starts each command in a new session (`start_new_session=True`) and kills the group on timeout. A new session also means Ctrl-C on the runner never reaches it: on 2026-10-04 a gate's `pytest` (and its Playwright driver) ran on for 16 hours after the runner stopped, reparented to systemd.
- Keep the new session (it is how a timeout kills the whole group). Kill the running group when `run_bounded` is left by an exception, `KeyboardInterrupt` included, and when the process gets SIGTERM.

### Done when
- a test: interrupting a `run_bounded` call (a `KeyboardInterrupt` raised while it waits) leaves no process of its group running
- a timeout still kills the whole group, as before
- `uv run runner check-all --task f7-04-gates-stop-with-runner` passes
