---
id: f3-13-stop-kills-agents
milestone: f3
depends_on: []
agent: lead
difficulty: 3
files:
  - runner/procs.py
tests:
  - tests/runner/test_procs.py
---

### Goal
When the runner stops (Ctrl-C, a crash, a kill), the agent it started stops with it, so nothing keeps editing the working tree.

### Context
Read `runner/procs.py` (`run`, `run_streaming`: both start the agent with `start_new_session=True` and only `killpg` on a timeout) and `tests/runner/test_procs.py`. Test-first.
- **What happened (2026-10-03, about 13:00):** the owner pressed Ctrl-C during f3-07's attempt 2. The runner stopped, but its `opencode run` (its own session, so Ctrl-C never reached it) kept going for about 15 minutes. It edited `factory_dashboard/static/factory.js`, `factory_dashboard/templates/line.html`, `factory_dashboard/static/dashboard.css` and the tests in the working tree, which the lead had meanwhile checked out on main. The lead's next commit swept the edits into main, and the lead took them out again (13336f3).
- **On any exception leaving the wait** (`KeyboardInterrupt`, `SystemExit`, others), `killpg` the child's group with SIGTERM, wait up to 5 s, then SIGKILL, and re-raise. Also on SIGTERM to the runner itself (a handler that raises `SystemExit`).

### Done when
- a test starts a sleeping child through `run_streaming`, raises `KeyboardInterrupt` from the tick callback, and finds the child's process gone
- the same for `run`
- `uv run runner check-all --task f3-13-stop-kills-agents` passes
