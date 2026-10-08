---
id: f55-01-archive-settled-threads
milestone: f55-dismiss-all-conversations-where-the-related
difficulty: 4
depends_on: [f31-01-settle-and-reject]
agent: lead
files:
  - runner/metrics.py
  - runner/requests.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_requests.py
---

### Goal
Archive, once, the threads the owner settled before f31-01, and archive a merged card's thread when its merge is applied.

### Context
Read `docs/milestones/f55-dismiss-all-conversations-where-the-related.md` D2, D3 and D4, and `docs/milestones/f31-when-i-click-on-approve-plan.md` D1 and D3. In `runner/requests.py`: `_archive`, `_merged`, `apply_requests`. In `runner/metrics.py`: `MIGRATIONS`, `open_db`, `set_thread_archived`, `open_owner_items`, `resolve_owner_item`. In `runner/tasks.py`: `short_key`. f31-01 adds the proposal state function to `runner/planner.py` and the `archived_why` column; use both.
- **Once:** the clear-out runs a single time per database, at the runner's first start after this lands. Choose how it records that it ran (a schema version step is the natural place); it must not run again after the owner opens a thread.
- **Which threads:** open (`archived` NULL), not `general`, card ready, building, needs sign-off or done in `milestones`, or with no row there (merged or removed), and no proposal of the latest set `open` by the state function.
- **Protected work: test-first.**

### Done when
- a thread on a ready card whose plan was approved, its lead reply the last message, is archived as `approved` with its `planning` item resolved, and leaves "Your answers wanted"
- a merged card's thread (no `milestones` row, `_merged`'s line last) is archived the same way
- a thread on a ready card whose latest set has an open `replan` stays open
- an idea or planning card's thread, and the general thread, stay open
- a thread the owner opens again after the clear-out is not archived by a later start
- applying a merge archives the duplicate's thread as `approved` after its line; the kept card's thread is untouched
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
