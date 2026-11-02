---
id: f106-04-lead-looks-at-a-block
milestone: f106-where-do-blocked-tickets-go-for
difficulty: 7
depends_on: [f106-01-blocked-reaches-the-owner, f106-06-red-main-blocks-nothing]
agent: lead
files:
  - runner/loop.py
  - runner/planner.py
  - runner/requests.py
  - runner/metrics.py
  - factory_dashboard/templates/thread.html
  - docs/workflow.md
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_planner.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
When the runner blocks a ticket of a card, it queues one planner job on that card's thread, so the lead reads the failed work and proposes a fix (ADR 29 items 1, 2, 4, 5, 6).

### Context
Read `.softfield/adr/29-the-lead-looks-at-a-blocked-ticket.md` (every item; it must be Accepted) and `.softfield/cards/f106-where-do-blocked-tickets-go-for.md` (D2). Then `block` and `run_planner` in `runner/loop.py`, `_plan_message` and `_plant` (how the runner writes a thread's first message and queues its planner row) in `runner/requests.py`, and the prompt in `runner/planner.py`. `runner/**` is protected: write the tests first.
- `block` writes the runner's message on the ticket's card's thread and queues its planner row. The message names the ticket, the reason, the branch (`task/<id>`, or `escalation/<id>`) and the run's log folder, and asks for what went wrong and a fix as a replan.
- The message is stored and shown as the runner's, never as the owner's words: it isn't a request of the owner's, can't show under "Didn't go through", and the thread's page labels it "The runner".
- The job may read the branch: its commands already allow `git diff`, `git log` and `git show`.
- No look for a ticket of the standing key bugs (no card, item 6), nor when the metrics database is absent.
- An archived thread opens again, as for an owner's message.
- The planner's prompt gains what a look is, in two lines at most.

### Done when
- a lead ticket of a card is blocked: its thread holds one new message from the runner with the ticket, the reason and the branch, and one planner row is queued for it
- that message shows on the thread's page as the runner's, and is in neither "Didn't go through" nor "Your answers wanted" before the lead replies
- the planner job for it runs as any other (parks at a limit, replies with points and proposals, then the thread is in "Your answers wanted")
- a blocked bug ticket queues nothing and writes no message
- blocking with no metrics database still blocks the ticket
- `docs/workflow.md` says what follows a block
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
