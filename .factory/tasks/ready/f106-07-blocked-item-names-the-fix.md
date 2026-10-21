---
id: f106-07-blocked-item-names-the-fix
milestone: f106-where-do-blocked-tickets-go-for
difficulty: 5
depends_on: []
files:
- factory_dashboard/planning.py
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f106-where-do-blocked-tickets-go-for-F2
---

### Goal
A blocked ticket on the owner's desk says where the lead's look stands: the lead is looking, or the lead's fix waits on the card's thread (F106 D4).

### Context
- `_blocked` in `factory_dashboard/planning.py` makes one `DeskItem` per open `blocked` owner item; its `words` are the reason alone ("check-all failed; the work is on task/f9-01-board").
- When the runner blocks a card's ticket it writes a message on the card's thread with author `runner`, whose text starts with "<ticket id> blocked:" (`planner.look_text` in `runner/planner.py`), and queues a `planner` job whose subject is `<card>#m<message id>` (`planner.look_subject`).
- Follow `_acted_on` in the same file: it replaces an item's `words`; here you only add to them.

### Steps
1. In `_blocked`, for each ticket, find the latest `planner_messages` row with `author = 'runner'` whose `text` starts with `"<ticket id> blocked:"`, on a thread of the same project (`planner_threads.project_id`).
2. If there is one and a `lead` message comes after it on the same thread: add ` · the lead's fix waits on F<n>'s thread` to the words, where `F<n>` is the thread's card upper-cased (`f9` → `F9`).
3. Else, if there is one: add ` · the lead is looking at it`.
4. Else: words unchanged (a bug ticket has no card, so no look).

### Tests
In `tests/factory_dashboard/test_planning.py`, beside `test_two_blocked_tickets_appear_second_on_the_desk_with_their_ids_and_reasons`, one test per case, checking `desk(...)`'s blocked group `words` exactly:
- runner message only → "<reason> · the lead is looking at it"
- runner message then a lead message → "<reason> · the lead's fix waits on F9's thread"
- no runner message → "<reason>"
- a runner message about another ticket on the same thread doesn't count for this one.

### Done when
- the four tests pass and would fail without the change
- all gates pass
