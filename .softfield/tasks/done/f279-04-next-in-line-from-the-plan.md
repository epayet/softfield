---
id: f279-04-next-in-line-from-the-plan
milestone: f279-i-would-like-to-be-able
difficulty: 3
depends_on: [f279-03-the-queue-page, f132-02-overview-live-every-project]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Queue panel takes its count, its sentence and Next in line from the runner's stored plan, the same as `/queue`, and links to the whole queue.

### Context
Read `.softfield/cards/f279-i-would-like-to-be-able.md` (D7) and the Overview picture in the Proposed side of `.softfield/cards/f279-mockup/queue.html`.
- Today Next in line comes from `live_line`'s `["now"]["next"]` (`factory_dashboard/line.py`, from `queries.run_order`) and the count from `queue` in `factory_dashboard/overview.py`, two orders (`.softfield/tasks/later/bug-42-queue-count-and-next-agree.md`). f132-02 has made both cover every project.
- Read `latest_queue_plan` in `runner/metrics.py`: the panel shows the plan's sentence on one line, the count of its ticket lines, and its first rows (the jobs, then three tickets), in the existing row markup; then "The whole queue ›" to `/queue`.
- With no plan stored, the panel reads as before this ticket.
- The floor's own queue (`live_line`) is not this ticket's.

### Done when
- the panel's count, its rows and `/queue`'s first rows agree, in the same order
- the sentence shows under the count, as on `/queue`
- "The whole queue ›" opens `/queue`
- with no plan stored, the panel reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 4803
gate_failures: []
tokens: 3343556
```
