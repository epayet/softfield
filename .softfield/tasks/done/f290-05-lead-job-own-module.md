---
id: f290-05-lead-job-own-module
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 5
max_diff: 5000                      # a move counts its lines twice: removed and added
depends_on: [f290-04-developer-job-own-module]
commands: [cp, sed -i]
files:
  - runner/loop.py
  - runner/lead_job.py
  - runner/developer_job.py
  - runner/session.py
  - tests/runner/test_loop.py
  - tests/runner/conftest.py
tests:
  - tests/runner/test_lead_job.py
---

### Goal
A lead ticket's job and an escalation (the headless lead, its settling, the ticket repair and the branch's finish) live in `runner/lead_job.py`, with their tests in `tests/runner/test_lead_job.py`; nothing the runner does changes.

### Context
Read the Decisions in `.softfield/cards/f290-runner-loop-py-is-6-500.md` (D1–D8), and follow f290-04's commit (`git log -1 --stat`).
- The candidates in `runner/loop.py`: `def _settling` (near the top, only the lead's jobs use it), from `def run_lead_task` to the end of `def _settle_lead_task`, and from `def _only_docs_and_tasks` to the end of `def _finish_branch` (`def handle_escalation`, `def _settle_escalation`, `def _repair_ticket`, `def _repair_requeue`, `def _ticket_problems`, `def _written_tickets`), applying D3.
- `def keep_blocked_work` stays in `runner/loop.py`: only `move_to_ready`, `set_aside` and `runner/requests.py` call it, none a job module (D3). `runner/requests.py` is untouched by this ticket.
- `runner/lead_job.py` imports from `runner/developer_job.py` at module level what f290-04 left there for it (`block`, `_logs_dir`, `_check_results`, `_check_all`, `_merged_line`) and from `runner/session.py` `_has_branch` and `_catch_up`. It calls `rate_finished` through an in-function `from runner import loop` (`# runner.loop imports this module`) until f290-06. f290-07's checkpoint calls `_written_tickets` and `_repair_ticket` from here.
- f290-04 left a function-level import of `run_lead_task` in `runner/developer_job.py`: point it at `runner/lead_job.py`, still inside the function (D4: `lead_job` may import `developer_job`'s helpers at module level, not the reverse).
- D5: `handle_escalation` is called by `run_queued` in `runner/loop.py`, so its tests keep patching it on `loop`; `_ticket_problems` is called inside `lead_job`, so tests patch it there.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`; check with `git diff --stat`.
- Then D7 for each moved name.

### Done when
- `runner/lead_job.py` holds the lead's ticket and escalation jobs, at most 1,800 lines, and does not import `runner/loop.py` at module level
- the moved tests pass in `tests/runner/test_lead_job.py`, none renamed or edited beyond imports and patch targets, and every other test in `tests/runner/` passes
- no ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or `class` beside `runner/loop.py`
- all gates pass (see `docs/workflow.md`), mypy included

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
