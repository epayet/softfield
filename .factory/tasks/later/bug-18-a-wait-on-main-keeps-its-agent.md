---
id: bug-18-a-wait-on-main-keeps-its-agent
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 43
finding: f153-i-wonder-if-sonnet-would-be-F2
files:
  - runner/loop.py
  - runner/state.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A lead ticket whose Opus step-up waited on a red main settles as Opus, with its true attempt count, once main passes.

### Context
Read `def _main_is_red`, `def run_lead_task` and `def _settle_lead_task` in `runner/loop.py`, and `waits_on_main` in `runner/state.py`. `runner/**` is protected: tests first.
- Today `waits_on_main` keeps only the branch, so when main passes the ticket is routed by its difficulty again: the merge names Sonnet, the footer says 1 attempt, and a failure there buys a second Opus step-up.
- Keep the agent and the attempt count with the branch, and settle as that agent. A state file written before the change (a plain branch) still loads.

### Done when
- an Opus step-up that waited on main merges as Opus, with `attempts: 2` in the footer
- a failure after that wait doesn't start another step-up
- a state file with the old shape loads and its wait settles as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
