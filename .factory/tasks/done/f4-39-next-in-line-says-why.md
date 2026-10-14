---
id: f4-39-next-in-line-says-why
milestone: f4-always-on
difficulty: 2
depends_on: []
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/queue.html
  - tests/factory_dashboard/test_overview.py
tests:
  - tests/factory_dashboard/test_overview.py
finding: f4-always-on-F1
---

### Goal
On the Overview, each "Next in line" row whose ticket waits says what it waits for: "waits for f1-04-live", "waits for f1-12-escalated's escalation" or "waits for Claude".

### Context
Read `queue` and `_live_context` in `factory_dashboard/overview.py`, `factory_dashboard/templates/_partials/queue.html`, `write_queue` and `queue_claude_client` in `tests/factory_dashboard/conftest.py`, and the queue tests in `tests/factory_dashboard/test_overview.py` (`WAITS`, `test_next_in_line_is_the_first_three_of_the_run_order`).
- Facts: `queue(conn, project, now)` already computes each ticket's `waits_for` (f4-08), but since f3-05 no page shows it: the Queue panel only uses its length. The "Next in line" rows come from `next` in `_live_context` (the line's run order); each row has a `ticket`, except a due review, which has none.
- In `_live_context`, pass the reasons by ticket id (from the `queue` list it already builds) to the template; in `factory_dashboard/templates/_partials/queue.html`, a row whose ticket has a reason ends with ` · ` and the reason. A row with no reason is unchanged.
- With `queue_claude_client`, the first three rows are tickets that wait for nothing. In your test, set `f1-05-first`, `f1-06-second`, `f1-10-queued` and `f1-11-waits-done` to `state="done"` with `metrics.upsert_ticket` on the fixture database (it changes only the fields you give), so the waiting tickets come up into Next in line. Check the order you get by running the test, not from this ticket.

### Done when
- with `queue_claude_client` and those four tickets done, `/live`'s `#queue` shows each of `f1-14-lead`, `f1-12-waits-running` and `f1-13-waits-escalated` in its own Next in line row together with its own reason, and no row carries another ticket's reason
- with `queue_client`, no Next in line row says "waits for"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 1553
gate_failures: ['stopped', 'stopped']
tokens: 876742
```
