---
id: f232-02-coming-row-says-when
milestone: f232-i-can-t-edit-a-seed
agent: developer
difficulty: 1
depends_on: [f232-01-plants-wait-two-minutes]
files:
  - factory_dashboard/coming.py
tests:
  - tests/factory_dashboard/test_coming.py
---

### Goal
A waiting plant's row in Coming seeds says when it will be planted while the runner still holds it.

### Context
Read D1 in `.softfield/cards/f232-i-can-t-edit-a-seed.md`, then `coming` in `factory_dashboard/coming.py` (it builds each `WaitingPlant` with the words "planting at the runner's next pick") and how `tests/factory_dashboard/test_coming.py` adds plant requests.
- Import `PLANT_HOLD` from `runner.requests`, as `coming.py` already imports other names from there.
- A plant with no `subject` whose `created` plus `PLANT_HOLD` is after `now` says "planting in about N min", with N the minutes left rounded up (at least 1). After that, and for a plant with a `subject`, it keeps "planting at the runner's next pick".
- "changed · …" before the words, for a plant with an edit on its way, stays as it is.

### Done when
- a plant created 30 seconds before `now` says "planting in about 2 min"
- a plant created 3 minutes before `now`, and a plant with a `subject`, say "planting at the runner's next pick"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
