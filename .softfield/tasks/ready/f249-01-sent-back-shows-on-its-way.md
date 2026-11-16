---
id: f249-01-sent-back-shows-on-its-way
milestone: f249-a-plan-is-being-sent-back
agent: developer
difficulty: 2
depends_on: []
files:
  - factory_dashboard/planning.py
  - factory_dashboard/thread.py
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
When the owner presses Send back on a proposal, the card's box in Your answers wanted shows on its way (dashed orange, "being revised") at once, and the thread page shows the comments they sent as their waiting message, as an owner's message does today.

### Context
Read "Plan" and D1 to D3 in `.softfield/cards/f249-a-plan-is-being-sent-back.md`.
- In `factory_dashboard/planning.py`: `_asked` lists the cards of open `plan_message` requests; a `send_back` request's subject is `<card>/<proposal id>` (`SEND_BACK` in `runner/requests.py`). `_listed` keeps proposals whose `proposal_state` (`runner/planner.py`) is `OPEN` or `ON_ITS_WAY`; `SENT_BACK` is the state after a send-back.
- In `factory_dashboard/thread.py`: follow the loop under "Append open plan_message requests as waiting messages"; a `send_back` value has the same `{text, comments}` shape, read by `message`.
- Tests to follow: `test_a_box_whose_message_waits_for_the_lead_is_dashed_and_keeps_its_links` in `tests/factory_dashboard/test_planning.py`, and the thread tests in `tests/factory_dashboard/test_thread.py` that add an open `plan_message`.

### Done when
- with an open `send_back` on a card's plan, the card's box on `/planning` is dashed, says "being revised", is left out of `waiting_for_you` and the desk's count, and still links the sent-back proposal, dashed
- the same holds after the runner has picked the send-back up and before the lead replies
- the thread page lists an open `send_back` as the owner's waiting message with its comments as numbered points, and shows the lead's reply as pending
- a card with no send-back and no message looks as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
