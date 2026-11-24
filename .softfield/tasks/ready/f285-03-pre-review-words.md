---
id: f285-03-pre-review-words
milestone: f285-i-think-i-said-at-some
depends_on: [f285-01-pre-review-job]
agent: developer
difficulty: 1
area: factory
files:
  - factory_dashboard/overview.py
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The dashboard names Copilot's new pre-review job in plain words where it already names a checkpoint.

### Context
Read D5 in `.softfield/cards/f285-i-think-i-said-at-some.md`. In `factory_dashboard/overview.py`, `ROLE_LINES` gives a ticketless job's line by its role; in `factory_dashboard/milestones.py`, `_ROLE_LABELS` names a role's group on a milestone's page. The new role is `pre-review`.
- `ROLE_LINES["pre-review"]` is "Copilot reads {key} before the lead's review".
- `_ROLE_LABELS["pre-review"]` is "Copilot's pre-reviews".
- No element is added, moved or removed.

### Done when
- `job_card("pre-review", "f5-board", "Board")` returns the line "Copilot reads F5 before the lead's review"
- a milestone page with a `pre-review` job lists it under "Copilot's pre-reviews"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
