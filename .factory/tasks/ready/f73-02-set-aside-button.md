---
id: f73-02-set-aside-button
milestone: f73-i-want-to-be-able-to
difficulty: 4
depends_on: [f73-01-set-aside-list, f42-01-review-page-room]
files:
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
Every proposal's review page has a "Set aside" button that takes the conversation off the desk with its drafts kept, and a proposal that has waited says how old its draft is.

### Context
Read `.factory/cards/f73-i-want-to-be-able-to.md` (D2, D4, D5). In `factory_dashboard/templates/proposal.html`: `#actions` and its `.action-buttons` block with `#send-back` and `#primary`; the review page is the route `/planning/{thread}/proposals/{id}` in `factory_dashboard/planning.py`. In `factory_dashboard/templates/thread.html`: the `#archive-button`, the example to copy (it posts the `archive` request, shows on its way and goes). Follow `test_archive_posts_once_and_the_button_goes` and `test_an_archive_on_its_way_shows_at_once_and_its_button_goes` in `tests/factory_dashboard/test_planning.py`.
- The button, `#set-aside-button`, under `#primary`, in the quiet style of the thread's Archive button (not the yellow of Approve), at least 44 px tall. It posts the same request as Archive: kind `archive`, subject the thread, value `on`. Nothing changes in `factory_dashboard/requests.py` or the runner.
- Beside it, one line: "It leaves your desk with its drafts kept. Planning lists it under Set aside; a message from you opens it again."
- It sets the whole conversation aside, not one proposal: the drafts of a reply live together on the card's branch.
- On its way: after the press the block is marked as the other buttons mark it (`on-its-way` on `#actions`) and the button is disabled.
- No button on a proposal already approved, rejected or applied, nor when the thread is archived already.
- **Refresh:** a second quiet button, `#refresh-button`, "Refresh against main", on a plan, mock-up or replan still open. It posts what Send back posts (kind `send_back`, the same subject) with the fixed text "Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets." and no comments, so the lead revises the drafts without the owner typing. It shows on its way as Send back does.
- **The stale note:** the page function in `factory_dashboard/planning.py` gives the template the days since the lead's message that holds this proposal. From 3 days on, a line beside Approve reads "Drafted N days ago: the code may have moved. Refresh it before approving.", beside the Refresh button Under 3 days, nothing.

### Done when
- an open plan's review page has `#set-aside-button`, whose `hx-vals` hold kind `archive`, the thread as subject and value `on`
- in Chromium, pressing it posts one `archive` request and the button can't be pressed again
- a proposal already approved, and one on an archived thread, have no `#set-aside-button`
- an open plan's page has `#refresh-button`, whose values are kind `send_back`, the proposal's subject and the fixed text; pressing it in Chromium posts one request; an ADR's and a merge's pages have none
- a proposal whose message is 5 days old shows "Drafted 5 days ago"; one from today shows no such line
- at 390 px the button is at least 44 px tall and inside the page's width
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
