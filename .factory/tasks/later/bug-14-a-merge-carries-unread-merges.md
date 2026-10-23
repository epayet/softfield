---
id: bug-14-a-merge-carries-unread-merges
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 38
finding: f49-don-t-ask-me-to-merge-F2
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
When a card is merged into a third card before its next planner job, the third card's job still reads what was merged into the first.

### Context
Read `def _merged` and `def _merge` in `runner/requests.py`, and the tests beside `test_a_merge_keeps_the_duplicates_words_then_the_leads_summary_of_its_thread` in `tests/runner/test_requests.py`. `runner/**` is protected: tests first.
- B is merged into A; before A's planner job, A is merged into C. B's history stays in A's thread's `merges_unread`, and C's job reads only A's own thread. The summary is still on C's card doc.
- In `_merged`, carry the duplicate's unread merges over to the kept thread.

### Done when
- B into A, then A into C: C's thread has both A's and B's merges unread, and its next planner job reads both
- a single merge reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
