---
id: bug-13-merge-export-keeps-the-last-reply
milestone: bugs
difficulty: 5
depends_on: []
agent: lead
area: factory
priority: 37
finding: f49-don-t-ask-me-to-merge-F1
files:
  - runner/loop.py
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
---

### Goal
When the lead merges a card from its own thread, the thread's export in `.factory/planning/` ends with the reply that proposed the merge and the "merged into" line.

### Context
Read `def _auto_merge` in `runner/loop.py` and `def _merge` and `def _export` in `runner/requests.py`, and `test_a_merge_keeps_the_duplicates_words_then_the_leads_summary_of_its_thread` in `tests/runner/test_requests.py`. `runner/**` is protected: tests first.
- Today `_merge` exports the thread before `run_planner` stores the reply that proposed the merge, so the export lacks that reply. The owner's words are all there and the database keeps the reply. The existing test stores the reply first, so it can't show this.
- Fix: store the reply before `_auto_merge` runs and update its proposals once the merge is applied (or pass the reply's text to `_export`).

### Done when
- a merge proposed on the duplicate's own thread exports a file whose last lead message is that reply, followed by the "merged into" line
- a merge proposed on another thread exports as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
