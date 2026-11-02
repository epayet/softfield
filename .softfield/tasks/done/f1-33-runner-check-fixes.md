---
id: f1-33-runner-check-fixes
milestone: f1
depends_on: [f1-07-replan-foundation]
agent: lead
difficulty: 3
files:
  - runner/tasks.py
  - runner/checks.py
  - runner/gates.py
  - runner/loop.py
  - runner/report.py
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_checks.py
  - tests/runner/test_loop.py
---

### Goal
The gates run every test that already passes, and `uv run runner run --dry-run` works on a lead ticket's branch.

### Context
Found by f1-07 (Replan log in `docs/milestones/f1.md`). Test-first.
- **Skipped tests:** `queued_tests` in `runner/tasks.py` (used by `check_all` in `runner/checks.py` and `gate_all_tests` in `runner/gates.py`) skips the `tests:` of every other ticket in `ready/`, `escalated/` and `blocked/`, even a file the current ticket lists itself. ADR 01 item 1 made the skip for developer tickets' skeleton tests, which fail on main until their ticket is done. Lead tickets write their own tests in their own job, so theirs are never skeletons, yet f1's lead tickets list existing files (`tests/runner/test_loop.py` by four of them, `tests/factory_dashboard/test_queries.py`, `tests/runner/test_report.py`): no gate has run them since f1 was queued. The fix, within ADR 01's intent: skip only other queued **developer** tickets' tests, and never the current ticket's own.
- **What slipped through:** `test_task_merges_on_first_attempt` in `tests/runner/test_loop.py` fails on main. f1-06 shrank the session report (`render` in `runner/report.py`) to a summary and the run's dashboard link, and the merge commit it checks for is no longer in it. The run's page (f1-14) shows the commits; decide whether the summary keeps them, and make the test match.
- **Dry run:** `run_session` in `runner/loop.py` calls `open_session`, which refuses anything but a clean main and makes a run folder, even for `--dry-run`. The replans (f1-19, f1-32) run it on their own branch: it should read `tasks/` and print the plan from any branch or tree, and create nothing.

### Done when
- with a developer ticket and a lead ticket queued, only the developer ticket's tests are skipped, and a ticket's own tests are never skipped
- `uv run pytest tests/runner tests/factory_dashboard` passes on the branch
- `--dry-run` on a branch with uncommitted changes prints the plan, and no run folder or database row appears
- `uv run runner check-all --task f1-33-runner-check-fixes` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
