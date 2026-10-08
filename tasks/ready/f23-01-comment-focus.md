---
id: f23-01-comment-focus
milestone: f23-when-i-click-comment-on-the
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
area: factory
---

## Goal
On a planning thread, tapping a point's "Comment…" puts the cursor in that point's comment box.

## Context
- `factory_dashboard/templates/thread.html`: each point of the latest reply has a `<details>` whose summary is "Comment…" and whose body is a `textarea.comment`. Nothing focuses it, so the owner taps twice.
- The example: `factory_dashboard/templates/proposal.html` focuses its box when its "Comment…" button opens it.
- After Send, the page reloads `#conversation` in place with `htmx.ajax`, so new `<details>` replace the old ones: listen for the click on `document`, not on each summary.
- On a phone (iOS Safari) the keyboard only comes up when the focus happens inside the tap itself. The `toggle` event fires after it, too late. So in the summary's click handler: `preventDefault()`, flip `details.open` yourself, and when it opened, focus the textarea right there.
- Browser test example: `test_a_comment_turns_the_primary_button_into_send_back` in `tests/factory_dashboard/test_planning.py`.

## Done when
- Clicking a point's "Comment…" opens its box and the focused element is that point's `textarea.comment`.
- Clicking it again closes the box and keeps the typed text.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

Keep the `<details>`: only add the focus on open.
