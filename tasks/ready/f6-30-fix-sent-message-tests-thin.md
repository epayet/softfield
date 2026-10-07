---
id: f6-30-fix-sent-message-tests-thin
milestone: f6-planning-room
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f6-planning-room-C3-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f6-21-sent-message's tests: they never check the waiting message's page, only that the typed text appears.

### Context
By the lead at a checkpoint, on the merge of `tasks/done/f6-21-sent-message.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f6-planning-room-C3-2, should-fix: in `tests/factory_dashboard/test_planning.py`, `test_send_with_comments_posts_one_request` (about line 437).

### Finding
f6-planning-room-C3-2: the merge changed one browser test's wait and added no test of the page the ticket describes.
> The Done when asks for a page with an open `plan_message` request to show its text as the owner's latest message with "Sent", show `#waiting`, and have no `#reply`; and, once the request is done and its `planner_messages` row exists, the text once as an ordinary message. None is tested: the browser test waits for the typed text anywhere in `#conversation` and for `#reply` hidden, so it passes without "Sent", the `#waiting` paragraph, the dashed edge, or the comment points. Assert within the message's element and within `#waiting`, on text with tags stripped and entities unescaped (`_text`).

### Done when
- a page-level test with an open `plan_message` request (text and one comment): the owner's message element has the text, "On N: <comment>" and "Sent", a dashed hazard border in its style, `#waiting` is present and `#reply` is absent
- a page-level test where the request is done and its `planner_messages` row exists: the text shows once, with no "Sent" and no dashed border
- the browser test also asserts `#waiting` shows and the message's "Sent" line, after Send, without a reload
- each finding above no longer holds: the tests check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
