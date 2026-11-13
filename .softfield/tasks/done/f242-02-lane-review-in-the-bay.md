---
id: f242-02-lane-review-in-the-bay
milestone: f242-the-review-of-a-fast-lane
difficulty: 3
depends_on: [f242-01-lane-review-goes-first]
files:
  - factory_dashboard/overview.py
  - tests/factory_dashboard/test_overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Next in line shows the queued review of a fast-lane card in the Fast lane bay, as the runner now takes it.

### Context
Read D4 in `.softfield/cards/f242-the-review-of-a-fast-lane.md`. The bay's picture is `.softfield/cards/f172-mockup/goes-first.html`; nothing new is drawn.
In `factory_dashboard/overview.py`: `queued_jobs` (its `card_keys` branch, from F191 D3, and the `lane` test on each pick), `_live_context` (builds `lane_keys`). `runner/dispatch.py` has `LANE_KINDS` and `plan`, from `f242-01-lane-review-goes-first`.
A review row's subject is its card's full key; `short_key` gives the short one, which `lane_keys` holds in capitals.
Tests to follow: the F191 D3 tests in `tests/factory_dashboard/test_overview.py` (an escalation of a lane card with no ready ticket).

### Done when
- An open review row for F172's full key, with F172 in the fast lane, shows in the Fast lane bay, above the planner jobs.
- The same row with F172 out of the lane, or on its way out, shows where it does today.
- The F191 D3 tests pass unchanged.

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 4716
gate_failures: []
tokens: 3887759
```
