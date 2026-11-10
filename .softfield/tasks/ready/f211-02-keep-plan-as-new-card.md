---
id: f211-02-keep-plan-as-new-card
milestone: f211-a-plan-must-not-get-lost
agent: lead
difficulty: 6
depends_on: []
files:
  - runner/requests.py
  - runner/planner.py
  - factory_dashboard/requests.py
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_requests.py
---

### Goal
A `keep_plan` request turns a card's open plan into a new idea card the lead is queued on, and the runner refuses to approve a plan on a card that is done.

### Context
Read `.softfield/cards/f211-a-plan-must-not-get-lost.md`: D3, D5, D6 and D8 are what this ticket builds. The state is D3's rule; the dashboard's pages are f211-03's and f211-04's.
- `runner/requests.py`: `_plant` is what Keep goes through, as a `plant` request whose value has `ask: true` (`planner.asks`), the way `_carry_on` writes a request and finishes it. `_apply` dispatches the kinds; `_latest` and `_settled` read a thread's list; `_close_if_settled` shows how a thread closes; `_approve_plan` is where D8's refusal goes.
- `runner/planner.py`: `proposal_state` and `_about` read the state, `WORKED` the results that count, `DRAFTED` the kinds, `seed_words` writes key points as thoughts, `plan_branch` names the branch. `_words` cuts a long title without refusing it.
- `factory_dashboard/requests.py`: `KINDS` is the list of what the dashboard may ask.

### Done when
- a `keep_plan` request on a thread with an open draft plants one idea card, titled from the plan proposal (else the first draft), without the title's leading "F51: " or "F51, "
- the new card's Notes say which card it was kept from, hold the proposals' key points, and name the plan branch with "check them against main before reusing them"
- the new card takes the old card's area, not the project's default (`planner.project_area`, F171 D5)
- the lead is queued on the new card's thread, and the old branch still exists
- each of the old list's drafts reads `planner.KEPT` from `proposal_state` once the request has worked, and on its way while it waits; a refused request leaves them open
- `_settled` counts a kept draft as settled
- the old thread gets a lead line naming the new card with its `/planning/<key>` path
- with every proposal of the list settled, an unarchived thread archives as `approved`; one the owner archived before stays archived, with reason `approved`
- a `keep_plan` on a thread with no open draft changes nothing and says why
- pressing Keep twice plants one card
- `_approve_plan` with drafts on a card whose doc on main is done returns "F51 is signed off: keep its plan as a new card" and leaves main and the branch unchanged; it says so before `loop.catch_up_plan` and the clash check (`clash_words`), so a done card's branch is never caught up or sent to Refresh; a merge-only approval on it still works
- an approval with `value` "first" (F224) is refused the same way
- `POST /requests` takes `keep_plan`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
