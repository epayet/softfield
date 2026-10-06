# Milestone F8: one visible queue

> **Status: planned** (2026-10-04, with the owner), on [ADR 22](../adr/22-one-visible-queue.md) (Accepted). **State:** ready · **Priority:** 2 · **Area:** factory
> The owner (2026-10-04): "the runner should be just running jobs, and most work should be visible there, an escalation, a review, a replan, an answer to my question". F6's planner jobs build on its picker (f6-01 depends on f8-03).

## Outcome
- Every job the runner will do is queued before it runs, with its reason, and the dashboard's queue shows them all in the order they will run: tickets, checkpoints, reviews, directions, escalations.
- One function picks the next job; `--dry-run` prints its list and reasons.
- Two switches on the allowance panel replace the reserve questions; the console no longer asks y/N.
- Nothing about what runs changes: the same caps, attempts, checkpoints and reviews.

## Decisions
- **D1 The table** (ADR 22 item 1): migration `_V6` in `runner/metrics.py`. `work_queue`: `id`, `project_id`, `kind` (checkpoint, review, direction, escalation, planner), `subject` (a ticket id or milestone key), `reason` (plain words), `created`, `not_before` (ISO or NULL), `started_job` (jobs.id or NULL), `done` (ISO or NULL). `runner/metrics.py` owns `queue_job`, `open_jobs` and `finish_queued`.
- **D2 The picker** (item 2): `runner/dispatch.py`, `pick(queued, tickets, windows, now) -> Pick(kind, subject, reason) | None`, pure. Kind order: planner, escalation, direction, checkpoint, review, then tickets as `pick_next` orders them (lead before developer while lead work is ready, as `lead_work_ready` says today). A row with `not_before` in the future is skipped with its reason.
- **D3 Parking** (item 2): a parked job is its queue row with `not_before`; `state.json`'s `parked` goes. The work branch and the session to resume stay as they are.
- **D4 The switches** (item 4, two, settled with the owner): request kind `reserve`, subject `week` or `five_hour`, value `on` or `off`, kept in `var/runs/state.json` with the time it was turned on. **On lasts 24 hours,** then turns itself off and raises a Needs-you item `reserve` ("turn it on again for 24 h?"). `uv run runner reserve week|five-hour on|off` does the same as the request, and `uv run runner run --use-reserve [week|five-hour]` turns one or both on for 24 hours as the command starts. Off is today's unanswered question; on is a yes. The console asks nothing.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | work-queue-table | L | 3 | – | D1 |
| 02 | dispatch | L | 6 | 01 | D2: the picker, reproducing today's order, and `--dry-run` from it |
| 03 | support-jobs-queued | L | 7 | 02 | the triggers queue rows; the loop runs what `pick` returns; D3 |
| 04 | reserve-switches | L | 5 | 01 | D4 in the runner |
| 05 | replan | L | 3 | 03, 04 | check 06–07, f5-18 and F6's tickets against 01–04; fix them; log it here |
| 06 | switch-buttons | D | 4 | 05, f3-25 | the two switches on the allowance panel, refreshed live (replaces f5-10; folds in f4-12 and f4-16) |
| 07 | queue-view | D | 4 | 05 | the Overview's queue lists queued jobs with their reasons |
| 08 | claude-rechecks-stand-in | L | 6 | 03 | merges only a stand-in checked wait in one queued Claude re-check (owner, 2026-10-06) |
| 09 | stand-in-fix-tickets | L | 6 | – | the stand-in's prompt and `fix_ticket`: one ticket per merged ticket and kind; test-only tickets for developers |
