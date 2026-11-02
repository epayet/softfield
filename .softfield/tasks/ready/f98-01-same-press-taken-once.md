---
id: f98-01-same-press-taken-once
milestone: f98-if-i-have-slow-internet-and
agent: lead
difficulty: 2
depends_on: []
files:
  - factory_dashboard/requests.py
  - runner/metrics.py
tests:
  - tests/factory_dashboard/test_requests.py
---

### Goal
A press the dashboard sends twice (the answer was lost on a slow connection and the owner pressed again) is stored once, so a note is never planted twice.

### Context
Read D2 in `.softfield/cards/f98-if-i-have-slow-internet-and.md`, then `ask` in `factory_dashboard/requests.py` and `add_request` in `runner/metrics.py`.
- Compare against the project's most recent `owner_requests` row only (highest id for that project): same `kind`, `subject` and `value` (NULL equal to NULL), and `created` less than 60 s before `now`. Then store nothing and answer with that row through `_status`, as for a new one.
- Anything else is stored as today. `add_request` itself keeps storing every call: the console's commands still make one row per ask.

### Done when
- two identical plants posted 5 s apart leave one `owner_requests` row, and both answers name the same request
- the same plant posted 61 s after the first is stored again
- pause, resume, pause posted within 60 s are three rows
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
