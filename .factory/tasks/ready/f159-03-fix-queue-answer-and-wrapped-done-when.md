---
id: f159-03-fix-queue-answer-and-wrapped-done-when
milestone: f159-there-s-a-bug-set-aside
agent: developer
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/tickets.py
tests:
  - tests/factory_dashboard/test_tickets.py
finding: f159-there-s-a-bug-set-aside-C2-1
---

### Goal
Fix two checkpoint findings on `f159-01-set-aside-ticket-page`: pressing "Queue it" shows no answer, and a wrapped "Done when" bullet loses its second line.

### Context
By the lead at a checkpoint, on the merges of `.factory/tasks/done/f159-01-set-aside-ticket-page.md` and `.factory/tasks/done/f159-02-ticket-notes-keep-their-lines.md`. What was found is under Finding.
- The example for the answer slot: the Queue button in `factory_dashboard/templates/tickets.html` (`hx-target="#answer-{{ t.ticket }}"`, with an empty `<div id="answer-…">` beside it).
- The example for wrapped lines: `_parse_blocks` in `factory_dashboard/tickets.py` (a non-bullet line after a bullet continues it).

### Finding
- C2-1, should-fix: in `ticket.html` the "Queue it" button has `hx-target="#ticket-aside-status"`, but that element exists only in the already-sent state, where the button is gone. With the button showing, the target is missing, so htmx drops the reply: the owner presses, the button disables and nothing says it went. No test presses the button.
- C2-2, should-fix: in `parse_ticket_body`, "Done when" keeps only lines starting `- ` whenever any exist, so a bullet wrapped onto an indented second line loses that line silently. The Goal and Context already join wrapped lines (f159-02); Done when does not.

### Done when
- with the button showing, the panel holds an empty element the button's `hx-target` names, so the reply has somewhere to land; a test reads the button's `hx-target` and finds that id in the same page
- a "Done when" of `- a bullet that wraps\n  over two lines\n- second` parses to `["a bullet that wraps over two lines", "second"]`, and the ticket page shows the full text
- the listed `tests:` pass, and fail without the change
- all gates pass
