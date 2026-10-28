---
id: f98-02-pressed-button-sends
milestone: f98-if-i-have-slow-internet-and
difficulty: 3
depends_on: [f98-01-same-press-taken-once]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/templates/tickets.html
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
Every dashboard button that asks the runner shows, from the press until the answer, that it is sending and can't be pressed again; when no answer comes it comes back and says to press again.

### Context
The picture to build: `.factory/cards/f98-mockup/pressed-buttons.html` (Proposed). The rule: D1 in `.factory/cards/f98-if-i-have-slow-internet-and.md`. Read the `htmx:beforeRequest` listener for Pause and Resume in `factory_dashboard/templates/base.html` (the example to follow: one listener on the document, failure listeners on the element), the tokens at the top of `factory_dashboard/static/dashboard.css` and `.lever.on-its-way`, and the Plant box and its `htmx:afterRequest` listener in `factory_dashboard/templates/planning.html`. For browser tests that hold or fail `/requests`, follow the ones in `tests/factory_dashboard/test_planning.py` and `tests/factory_dashboard/test_thread.py` that call `page.route("**/requests", …)`.
- One listener pair in `base.html`, for POSTs to `/requests` only. Add `--sending-belt` to the tokens in both themes and a `.sending` rule beside `.lever.on-its-way`, with the belt still under `prefers-reduced-motion`.
- Words, as `data-sending` on the buttons: Plant and Plant and ask the lead "Planting…", Save "Saving…", Cancel it "Cancelling…", Dismiss "Dismissing…", Remove (Remove seed) "Removing…", Send and Send to the lead "Sending…", Send back "Sending back…", Accept ADR "Accepting…", Approve plan and Approve merge "Approving…", Plant it "Planting…", Queue and Queue it "Queuing…".
- No answer within 30 s counts as a failure: set it on the request (`htmx.config.timeout` or the `timeout` event), not globally for the live polls. Failure words, in `--fail`, in the request's `hx-target`: "Didn't hear back from the factory. Your note is still here: press again, it won't be planted twice." where the form has a text box, else "Didn't hear back from the factory: press again."
- Leave alone what pages already do on press (Pause, Resume, Archive, Sign off, the reserve lever, a blocked ticket's Try again and Set aside, Reject's and Approve plan's on-its-way panel) and the board's and Projects page's `fetch` sends. They must still work.

### Done when
- with `/requests` held, pressing Plant on Planting turns it into "Planting…" with the `sending` class and disabled, disables Plant and ask the lead and makes the box read-only; a second press stores nothing
- with `/requests` held, Remove on a seed's thread shows "Removing…" and is disabled
- when `/requests` answers 400, or doesn't answer within the timeout (a test may shorten the 30 s from the page), Plant is back as "Plant", enabled, the note still in the box, and the status shows the failure words
- after a normal answer, Plant behaves as today: the note shows in Coming and the box is empty
- Pause and Archive still behave as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
