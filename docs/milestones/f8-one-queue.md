# Milestone F8: one visible queue

> **Status: planned** (2026-10-04, with the owner), on [ADR 22](../adr/22-one-visible-queue.md) (Accepted). **State:** building · **Priority:** 2 · **Area:** factory
> The owner (2026-10-04): "the runner should be just running jobs, and most work should be visible there, an escalation, a review, a replan, an answer to my question". F6's planner jobs build on its picker (f6-01 depends on f8-03).

## Outcome
- Every job the runner will do is queued before it runs, with its reason, and the dashboard's queue shows them all in the order they will run: tickets, checkpoints, reviews, directions, escalations.
- One function picks the next job; `--dry-run` prints its list and reasons.
- Two switches on the allowance panel replace the reserve questions; the console no longer asks y/N.
- Nothing about what runs changes: the same caps, attempts, checkpoints and reviews.

## Decisions
- **D1 The table** (ADR 22 item 1): migration `_V8` in `runner/metrics.py`. `work_queue`: `id`, `project_id`, `kind` (checkpoint, review, direction, escalation, planner), `subject` (a ticket id or milestone key), `reason` (plain words), `created`, `not_before` (ISO or NULL), `started_job` (jobs.id or NULL), `done` (ISO or NULL). `runner/metrics.py` owns `queue_job`, `open_jobs` and `finish_queued`.
- **D2 The picker** (item 2): `runner/dispatch.py`, `pick(queued, tickets, windows, now) -> Pick(kind, subject, reason) | None`, pure. Kind order: planner, escalation, direction, checkpoint, review, then tickets as `pick_next` orders them (lead before developer while lead work is ready, as `lead_work_ready` says today). A row with `not_before` in the future is skipped with its reason.
- **D3 Parking** (item 2): a parked support job is its queue row with `not_before`; what it needs to start again is `state.json`'s `queued`. A parked ticket stays in `state.json`'s `parked` (as built by f8-03: tickets aren't rows). The work branch and the session to resume stay as they are.
- **D4 The switches** (item 4, two, settled with the owner): request kind `reserve`, subject `week` or `five_hour`, value `on` or `off`, kept in `var/runs/state.json`'s `switches` with the time it was turned on. **On lasts 24 hours,** then turns itself off and raises a Needs-you item `reserve` ("turn it on again for 24 h?"). `uv run runner reserve week|five-hour on|off` does the same as the request, and `uv run runner run --use-reserve [week|five-hour]` turns one or both on for 24 hours as the command starts. Off is today's unanswered question; on is a yes. The console asks nothing.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | work-queue-table | L | 3 | – | D1 |
| 02 | dispatch | L | 6 | 01 | D2: the picker, reproducing today's order, and `--dry-run` from it |
| 03 | support-jobs-queued | L | 7 | 02 | the triggers queue rows; the loop runs what `pick` returns; D3 |
| 04 | reserve-switches | L | 5 | 01 | D4 in the runner |
| 05 | replan | L | 3 | 03, 04 | check 06–07, f5-18 and F6's tickets against 01–04; fix them; log it here |
| 06 | switch-buttons | D | 4 | 05, 10, f3-25 | the two switches on the allowance panel, refreshed live (replaces f5-10; folds in f4-12 and f4-16) |
| 07 | queue-view | D | 4 | 05 | the Overview's queue lists queued jobs with their reasons |
| 08 | claude-rechecks-stand-in | L | 6 | 03 | merges only a stand-in checked wait in one queued Claude re-check (owner, 2026-10-06) |
| 09 | stand-in-fix-tickets | L | 6 | – | the stand-in's prompt and `fix_ticket`: one ticket per merged ticket and kind; test-only tickets for developers |
| 10 | reserve-request-kind | L | 2 | 05 | the dashboard's guard takes `reserve` instead of `five_hour` (from the replan) |
| 14 | reserve-lever | D | 3 | 06, f9-28 | each switch becomes a factory lever on its meter's line, "use reserve", its sentence in the legend; picture `f8-mockup/reserve-lever.html` (owner, 2026-10-09) |

## Replan
f8-05 (2026-10-06), against what f8-01…04 merged (`65ed894`, `b667f74`, `6fb1b62`, `801a4b1`):
- **D1:** the migration is `_V8`, not `_V6` (F5 took `_V6` and `_V7`).
- **D3:** only support jobs park as rows; a parked ticket stays in `state.json`'s `parked`, and a row's needs are in `state.json`'s `queued`.
- **D4:** the switches are `state.json`'s `switches`.
- **f8-06:** the state is `switches`, not `reserve`; named `load_state`, `switch_on`, `SWITCHES`, `set_switch` and how the dashboard finds the state file (`_config` in `factory_dashboard/line.py`, `runs_dir`). It now depends on f8-10.
- **New f8-10 (lead):** the dashboard's `POST /requests` (protected) took only `signoff`, `five_hour` and `queue`, so f8-06's `reserve` post would be 400 and a developer can't change the guard. It swaps `five_hour` (nothing posts it) for `reserve`.
- **f8-07:** the rows come from `open_jobs` and `Queued.from_row`, their order and "waits until …" from `dispatch.plan`; `_when` words a time as "Mon 5 Oct 17:00", not "HH:MM", so its Done when says "waits until" and the time. A row whose job is running is left out; a check of the kind order added.
- **f5-18:** the pause is a state of `pick`/`plan` (ADR 22 item 5), waited out in `work_queue` instead of `_wait_for_reset`, a resume taken during the wait as `take_switches` takes switches; `limit=False` named for the clog; a new `State` field, not `paused_until`; `runner pause` follows `_switch_request`; `KINDS` named. Files and tests gain `runner/dispatch.py`, `runner/state.py`, `runner/cli.py` and their tests; depends on f8-03 and f8-04; difficulty 4 → 5.
- **f6-01:** `_resume_support` is gone. Each `plan_message` becomes a `planner` row in `apply_requests` (`queue_job`), its subject per message since `enqueue` keeps one open row per kind and subject; `pick` already puts `planner` first; `run_queued` gets the branch; `claude_hold` keeps the owner's 25% back, so the planner's check uses both reserves; a hard limit parks its row (`park_row`). `runner/requests.py` and its tests added.
- Seen, not changed: `tasks/ready/f5-11-queue-priority.md` also reworks `queue` in `factory_dashboard/overview.py`; whichever of it and f8-07 runs second builds on the other.
