---
id: bug-21-dry-run-plans-with-the-runs-windows
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 47
finding: f8-one-queue-F4
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
`softfield run --dry-run` says of a job held by Claude's limits what the live run would do with it.

### Context
Read `def dry_run_plan` and `def work_queue` in `runner/loop.py`, and `plan` in `runner/dispatch.py`. `runner/**` is protected: tests first.
- The dry run plans with Claude's windows and limits, but the live loop picks with an empty `Windows()` and lets each job check them as it starts: the dry run can say a checkpoint "waits" while the run would do it with a stand-in, or park it.
- Word the dry run's Claude waits as "would park or go to a stand-in" (simplest), unless passing the run's own windows to its pick is as small.

### Done when
- with Claude at its limit and a checkpoint due, the dry run's line for it says it would park or go to a stand-in, not "waits"
- with Claude free, the dry run reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
