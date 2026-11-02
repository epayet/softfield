---
id: f143-01-proposal-page-own-module
agent: lead
milestone: f143-split-test-planning-py-by-page
difficulty: 3
max_diff: 2000                      # a move counts its lines twice: removed and added
depends_on: []
commands: [cp, sed -i]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/proposal.py
  - factory_dashboard/app.py
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_proposal.py
---

### Goal
The proposal review page and the mock-up route live in their own module, `factory_dashboard/proposal.py`, with their tests in `tests/factory_dashboard/test_proposal.py`; nothing they do changes.

### Context
Read the Decisions in `.softfield/cards/f143-split-test-planning-py-by-page.md` (D1–D5 apply to this ticket), `layout_problems` in `runner/gates.py`, and in `factory_dashboard/planning.py` the section from `# --- proposal review (f6-08)` to the end (`def mockup_file`, `class PlanChange`, `def _plan_changes`, `def _who`, `def proposal_review`).
- Move to `factory_dashboard/proposal.py`: that section, with its own `router`, included in `factory_dashboard/app.py` beside `planning.router`. Helpers the thread page or other modules also use (`_repo`, `_note`, `_adr_waits`, `_resolve_mockup_path`) stay in `planning.py` for now; f143-03 moves the thread's.
- Move to `tests/factory_dashboard/test_proposal.py`: the tests under `# --- proposal review page (f6-08)` and `# --- old-path resolved mockup (f165-01)` in `tests/factory_dashboard/test_planning.py`, with their own helpers (`_review`, `_review_page`, `_key_points`, `_changes`, `_replanned`, `ADR_ON_MAIN`). `_posts` and the other shared helpers stay in `test_planning.py` and are imported (D3); the `planning` and `checkout` fixtures move to `tests/factory_dashboard/conftest.py`.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>` rather than pasting it through Edit; check the result with `git diff --stat`.
- Then D5: Grep `.softfield/tasks/ready/`, `.softfield/tasks/later/` and `docs/agents/developer.md` for each moved name (`mockup_file`, `proposal_review`, `_plan_changes`, and every moved test's name) and point them at the new files.

### Done when
- `uv run pytest -q tests/factory_dashboard/test_planning.py tests/factory_dashboard/test_proposal.py` passes the same tests as `test_planning.py` did on main, none renamed or edited beyond its imports
- the review page and `/planning/mockups/...` answer exactly as before (their moved tests show it)
- no file in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or test beside `factory_dashboard/planning.py` or `tests/factory_dashboard/test_planning.py`
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
