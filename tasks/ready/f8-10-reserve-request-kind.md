---
id: f8-10-reserve-request-kind
milestone: f8-one-queue
depends_on: [f8-05-replan]
agent: lead
difficulty: 2
files:
  - factory_dashboard/requests.py
  - runner/requests.py
tests:
  - tests/factory_dashboard/test_requests.py
  - tests/runner/test_requests.py
---

### Goal
The dashboard may post a `reserve` request, the one f8-06's switches send, and no longer the `five_hour` answer they replace.

### Context
Read D4 in `docs/milestones/f8-one-queue.md`, `docs/security.md`, `factory_dashboard/requests.py` (the guard and `KINDS`) and `runner/requests.py` (`RESERVE`, `FIVE_HOUR`, `_five_hour`, `take_switches`). Test-first; `factory_dashboard/requests.py` is protected, so f8-06 (a developer's) can't add the kind.
- `KINDS` takes `RESERVE` in place of `FIVE_HOUR`. Nothing on the dashboard posts `five_hour`: it was f5-10's Yes/No, which f8-06's switches replace (ADR 22 item 4).
- Drop the `five_hour` kind from `runner/requests.py` (`FIVE_HOUR`, `_ANSWERS`, `_five_hour` and its branch in `take_switches`): an old open one finishes as "unknown request".
- The guard itself doesn't change.

### Done when
- a `reserve` post from the dashboard's own page writes its row, with its subject and value; the same post from another origin is 403
- a `five_hour` post is 400
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
