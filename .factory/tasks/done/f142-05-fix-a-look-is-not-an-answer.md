---
id: f142-05-fix-a-look-is-not-an-answer
milestone: f142-why-am-i-not-getting-notifications
difficulty: 3
depends_on: []
files:
  - runner/notify.py
  - runner/loop.py
tests:
  - tests/runner/test_notify.py
finding: f142-why-am-i-not-getting-notifications-F3
---

### Goal
The phone's notification after a planner job says what happened: the lead answered you, the lead looked at a blocked ticket, or the lead couldn't answer.

### Context
Read `run_planner` and `block` in `runner/loop.py` (each ends with a call to `_notify`), then `item_message` and the words at the top of `runner/notify.py`. Follow the tests in `tests/runner/test_notify.py`: `test_a_leads_reply_on_a_card_sends_that_the_lead_answered` for a planner job, and `test_a_blocked_lead_ticket_of_a_card_gets_one_look_on_its_thread` in `tests/runner/test_loop.py` for a blocked ticket and its look.
- Today every planner job sends "The lead answered you", also the runner's own look at a blocked ticket (`looked` in `run_planner`, ADR 29), where the owner wrote nothing, and a job that failed.
- New words in `runner/notify.py`: "The lead looked at a blocked ticket" for a look, "The lead couldn't answer you" for a failed job (`result.ok` false). Both open the card's thread, as a reply does. A card title, a reply or a reason is still never in the words.
- `block` already sends "A ticket needs your decision"; nothing tests it.

### Done when
- a lead's reply that worked: "<project> · The lead answered you", as today
- a look at a blocked lead ticket of a card: the block sends "<project> · A ticket needs your decision" opening the Overview, then the look sends "<project> · The lead looked at a blocked ticket" opening the card's thread: two notifications, in that order
- a planner job that fails: "<project> · The lead couldn't answer you", opening the card's thread
- a ticket blocked again while its item is still open sends nothing
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
