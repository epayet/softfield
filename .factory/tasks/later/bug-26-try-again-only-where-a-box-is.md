---
id: bug-26-try-again-only-where-a-box-is
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 53
finding: f14-coming-planted-ideas-not-clickable-F4
files:
  - factory_dashboard/coming.py
tests:
  - tests/factory_dashboard/test_coming.py
---

### Goal
On the desk's "Didn't go through", a refused edit of a message offers Try again only once that message is done, when its thread has a reply box to take it.

### Context
Read `def _failed_edit` and `def _edited` in `factory_dashboard/coming.py`, and `test_an_edit_refused_for_its_words_shows_them_with_the_runners_reason` in `tests/factory_dashboard/test_coming.py`, whose Try again assertion changes with this.
- Today Try again opens the thread at `#reply`, where no reply box is drawn while the message still waits (`factory_dashboard/templates/thread.html` draws "Next for the lead" instead). The words stay on the desk and the message's own Edit is back, so nothing is lost.
- Give `again` only when the message the edit names is done.

### Done when
- an edit refused while its message waits: the item shows the words and the reason, and no Try again
- an edit refused after its message was answered: Try again opens the thread with the words in the box, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
