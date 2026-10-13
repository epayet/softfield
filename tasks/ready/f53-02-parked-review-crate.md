---
id: f53-02-parked-review-crate
milestone: f53-why-is-milestone-diff-review-waiting
difficulty: 3
depends_on: []
files:
  - factory_dashboard/line.py
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_overview.py
finding: f53-why-is-milestone-diff-review-waiting-F2
---

### Goal
A review that waits for Claude shows as waiting in the line's queue, behind the tickets that can run, instead of as number 1 with nothing said.

### Context
Since F53 the runner parks a due review Claude can't take: its `work_queue` row (kind `review`, subject the milestone's key) gets a `not_before`, and developer tickets run meanwhile. The dashboard doesn't know: `_due_reviews` in `factory_dashboard/line.py` still makes its crate with `"waits": []`, and `live_line` numbers it first.
- Read only `_due_reviews` and the `queue = [...]` lines of `live_line` in `factory_dashboard/line.py`, and the `{% for t in next %}` loop of `factory_dashboard/templates/_partials/queue.html`.
- The open rows: `metrics.open_jobs(conn, project_id)` (`runner/metrics.py`); in a test, `metrics.queue_job(conn, project, "review", "f8", "F8's tickets are all done", created, not_before)` makes one, with ISO strings.
- A review is parked when its open row's `not_before` is after `now`. Its crate's `waits` is then one string, `Claude's reset at 14:00` (the hour and minute of `not_before` in local time, `.astimezone()`): `factory_dashboard/static/factory.js` already draws a crate with `waits` dashed and titles it "(after …)".
- A review parked between two rounds has the milestone status `review`, not `review due`: it gets its crate from its parked row all the same. A milestone under review with no parked row gets none, as today.
- The examples to copy, one test each: `test_a_due_review_heads_the_queue_as_a_batch_crate` in `tests/factory_dashboard/test_line.py` (it calls `document(line_db)`, whose `now` is `LINE_NOW`) and `test_next_in_line_names_a_due_review_first` in `tests/factory_dashboard/test_overview.py`. **Don't read the rest of those two files or `tests/factory_dashboard/conftest.py`: copy the example and add the queued row.**

### Done when
- a due review whose row is parked until an hour after `LINE_NOW`: its crate's `waits` is `["Claude's reset at HH:MM"]`, it comes after every ticket crate whose `waits` is empty, and the numbers still run 1, 2, 3…
- a milestone with status `review` and a parked review row has the same crate; with no such row it has none
- a due review with no row, or one whose `not_before` has passed, heads the queue with `"waits": []`, as today
- on the overview, Next in line's batch row for a parked review ends with "· waits for Claude's reset at HH:MM"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
