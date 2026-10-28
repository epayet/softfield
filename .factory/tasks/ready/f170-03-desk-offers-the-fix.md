---
id: f170-03-desk-offers-the-fix
milestone: f170-there-s-a-blocked-ticket-that
difficulty: 3
depends_on: [f170-02-fix-after-try-again]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/coming.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A blocked ticket on the desk shows the lead's fix inside its item, with "Approve the lead's fix" as its yellow button, while "Try again as it is" and "Set aside" become the quiet ones.

### Context
Read `.factory/cards/f170-there-s-a-blocked-ticket-that.md` (D3) and the mock-up to build, `.factory/cards/f170-mockup/blocked-on-the-desk.html` (Proposed: both items).
- In `factory_dashboard/coming.py`: `DeskItem`; in `factory_dashboard/planning.py`: `_blocked`. `_blocked` already finds the runner's look on the card's thread and whether the lead replied after it. Add the fix's facts to the blocked item: the card's key (`f152`), the title of the lead's first point in that reply (`points`, a JSON list, of the `planner_messages` row), and the `replan` proposal of the thread's latest proposals (`metrics.latest_proposals`): its title and how many key points. No replan in the reply: the item says the lead's fix waits on the thread, as today.
- The words under the ticket keep the runner's reason and "· N tickets wait behind it", without "its work is on task/…" and without today's "· the lead's fix waits on F152's thread" or "· the lead is looking at it": the plate says those now. Change the two tests that assert today's words (`test_runner_message_only_says_lead_is_looking`, `test_runner_message_then_lead_says_waits_on_thread`).
- In `factory_dashboard/templates/planning.html`, the `blocked` group's `article.blocked-ticket`: the "The lead's fix" plate under the link, as the mock-up draws it (its stripe and corner tick use `--hazard`, `--hazard-ink` and `--ink-2` only); "read it on F152's thread ›" links to `/planning/f152`.
- "Approve the lead's fix" posts what the Approve plan button of `factory_dashboard/templates/proposal.html` posts (`approve_plan`, the card's key as `subject`) and shows the item on its way with `blockedOnItsWay(this, 'Approving the lead's fix at the runner's next pick')`. "Try again as it is" posts today's `queue` request, with the caveat line under the buttons.
- While the lead is still looking: the plate says "The lead is reading the work and its logs; its fix comes here", and the buttons are "Try again as it is" and "Set aside", both quiet. A bug ticket (no card, no look) keeps today's item and buttons.

### Done when
- a blocked f9-01-board whose card's thread has the runner's look then a lead reply with a `replan` "F9: rework the board" of 3 key points, first point "What went wrong: the test run was cut": the item shows that first point, "F9: rework the board · 3 key points", a link to `/planning/f9`, and an "Approve the lead's fix" button posting `approve_plan` with subject `f9`
- the same item has "Try again as it is" posting `queue` for f9-01-board, and "Set aside"
- with the look but no lead reply yet: "The lead is reading the work and its logs; its fix comes here", no Approve button
- a lead reply with no replan: no Approve button, the plate says the lead's fix waits on F9's thread, with its link
- a blocked bug ticket: "Try again" and "Set aside" as today
- pressing Approve shows the item on its way at once, dashed orange, its buttons gone
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
