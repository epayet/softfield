---
id: bug-27-thread-send-draws-one-conversation
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 54
finding: f14-coming-planted-ideas-not-clickable-F3
files:
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
After a Send on a card's thread, the page has one `#conversation`, drawn again the way `factory_dashboard/templates/planning.html` draws its parts after a post.

### Context
Read the script after `#reply` in `factory_dashboard/templates/thread.html` (lines 185–208) and F14's listener a few lines below it (lines 219–225), and the listener in `factory_dashboard/templates/planning.html` (lines 205–232), the worked example. Lead ticket: the browser tests are in `tests/factory_dashboard/test_thread.py`.
- Today the reply form's listener is bound to `#reply` itself, waits 100 ms, and swaps the fetched `#conversation` `innerHTML` into the one on the page: two elements with one id after each Send (f13-F3, f14-F3). f13-01's developer copied it, as the worked example for "draw part of a page again after a post".
- Bind it on the document, as F14's listener is, with no timer and `swap: "outerHTML"`. The `input` listeners on `#reply` (the progress count, clearing `again`) are inside the swapped element, so they must keep working after a Send: check them.

### Done when
- after a Send, `page.locator("#conversation").count() == 1`, and the sent message shows
- after two Sends in a row, still one, and both show
- after a Send, typing a comment still updates the "points · comments" count
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
