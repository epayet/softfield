# Milestone F290: Split runner/loop.py into one module per job kind, with no change in behaviour

> **State:** ready · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-24.

## Notes
runner/loop.py is 6,500 lines and grows three lines for every one removed: plan splitting it by job kind (developer tickets, lead tickets, planner, reviews, waits) with no change in behaviour, one module per ticket.

## Plan (lead, 2026-11-24)
- **Why:** `runner/loop.py` is 6,813 lines and `tests/runner/test_loop.py` 9,342. Since 2026-08 the file gained about three lines for each one removed; 32 ready tickets name it, so every runner ticket opens the whole file to change one job.
- **The worked example is F143** (`.softfield/cards/f143-split-test-planning-py-by-page.md`): four lead "own module" tickets moved 1,400–3,400 lines each for $0.55–$1.39 and 10–19 minutes, with `cp` and `sed -i`, the tests moving with the code. This card does the same to the runner.
- **Six job modules, plus what they share.** The owner's five kinds (developer tickets, lead tickets, planner, reviews, waits) need a sixth piece under them: the session, the queue's rows, the job records and `call_claude`, which every kind uses. It moves first, because each later module imports it. Ratings fit no kind and `runner/ratings.py` says it is pure, so its database half gets its own module.
- **Tickets, each waiting for the one before** (all lead: `runner/` is protected): `f290-01-session-own-module`, `f290-02-waits-own-module`, `f290-03-replan-after-the-base` (ADR 16 item 7: the four later moves rely on what 01 and 02 built), `f290-04-developer-job-own-module`, `f290-05-lead-job-own-module`, `f290-06-rating-store-own-module`, `f290-07-review-job-own-module`, `f290-08-planner-job-own-module`.
- **No mock-up:** nothing on screen changes.

## Decisions
- **D1: seven modules, flat in `runner/`, imports one way (down the list):**
  ```
  runner/
    loop.py           the scheduler: work_queue, choose_ticket, run_queued, after_ticket,
                      run_session, run_projects, the idle line, update_live, dry_run_plan,
                      queue_ticket / set_aside                       ← tests/runner/test_loop.py
    planner_job.py    run_planner, run_setup, plan branches, drafts, auto-merge, work_stands
                                                                     ← tests/runner/test_planner_job.py
    review_job.py     checkpoint, shadow and stand-in checkpoints, pre_review, fix tickets,
                      record_findings, note_merge                    ← tests/runner/test_review_job.py
    lead_job.py       run_lead_task and its settling, handle_escalation, the ticket repair,
                      _finish_branch                                 ← tests/runner/test_lead_job.py
    developer_job.py  run_task, _develop, _regate, direction, _merge, red main, block
                                                                     ← tests/runner/test_developer_job.py
    rating_store.py   starting_ratings, standing, rate_ticket, rate_verdicts, rate_bench,
                      replay_ratings, void_benches_before            ← tests/runner/test_rating_store.py
    waits.py          Claude's holds and limits: switches, windows, fresh_reading, login,
                      Hold / claude_hold, park_review, passing over, wait_for_room
                                                                     ← tests/runner/test_waits.py
    session.py        Session, open/close_session, now/clock, in-flight, job records,
                      the queue's rows (enqueue, park, finish), routing, call_claude
                                                                     ← tests/runner/test_session.py
  ```
  The kind's `_job` suffix keeps them apart from the modules that hold a kind's parsing (`runner/planner.py`, `runner/review.py`, `runner/milestone.py`), which stay as they are. `runner/ratings.py` stays pure.
- **D2: move only.** No behaviour, name, signature, prompt or test body changes; every test keeps its name and passes. A test may change only its imports and its `monkeypatch` targets, or move file. Comments and docstrings move with their code.
- **D3: where a function goes:** to the one job module that uses it; to `runner/session.py` (or `runner/waits.py`, when it is about Claude's limits) when two or more job modules use it; it stays in `runner/loop.py` when only the scheduler uses it. A later ticket that finds a helper it shares with a module already moved moves it down to `runner/session.py` in the same commit.
- **D4: imports run one way:** `loop` → the `_job` modules → `rating_store` → `waits` → `session`. A module that needs one above it imports it inside the function, with the comment `# runner.x imports this module`, as `runner/loop.py` imports `runner.milestone` today. Other modules (`runner/cli.py`, `runner/milestone.py`, `runner/requests.py`, `runner/bench.py`, `runner/setup.py`, the tests) import each name from its new home; `runner/loop.py` keeps no alias for a name it does not call itself.
- **D5: one patch reaches every caller.** The names the tests patch that move to `runner/session.py` or `runner/waits.py` (`now`, `clock`, `set_activity`, `call_claude`, `fresh_reading`, `_notify`, `_windows_now`, `_passed_over`, `_held_at_the_limit`, `wait_for_room`, the `POLL_S`, `HEARTBEAT_EVERY` and `OPEN_RUNS` constants) are reached from other modules through the module (`session.now()`), never a from-import, and the tests patch them there (`monkeypatch.setattr(session, "now", …)`). A name imported from another package module (`run_gates`, `warmup`, `run_bounded`, `probe`) is patched on the module that now calls it. `runner/milestone.py`, `runner/requests.py` and `runner/cli.py` keep their own import style: only the module they import from changes.
- **D6: tests move with their code.** A test goes to the file of the module whose function it calls; one that drives `work_queue` or `run_projects` stays in `tests/runner/test_loop.py`. Helpers shared by test files stay in `tests/runner/test_loop.py` and are imported from it; fixtures used by more than one file go to `tests/runner/conftest.py`.
- **D7: each move points the tickets it breaks** (F143 D5): a ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/`, a worked example in `.softfield/developer.md`, and `AGENTS.md` or `runner/instructions/*.md`, that names a moved `def`, `class` or test beside `runner/loop.py` or `tests/runner/test_loop.py`, names the new file in `files:`, `tests:` and Context, in the same commit. ADRs and done tickets keep their history.
- **D8: sizes to land:** no new module over 1,800 lines, no new test file over 3,000; at the end `runner/loop.py` is the scheduler only, under 2,000 lines. `AGENTS.md` item 5 names the job modules as the runner's edges, with one line: a new job kind gets its own `_job` module; `runner/loop.py` only schedules.

## Replan (f290-03, 2026-11-25)
Checked against `runner/session.py` (1,728 lines), `runner/waits.py` (515), `tests/runner/test_session.py` (758), `tests/runner/test_waits.py` (75) and `runner/loop.py` as it stands (4,802; `tests/runner/test_loop.py` 8,536). Docs and tickets only; no Decision changed (nothing built contradicts one):
- **D3, as read for the four later moves:** a helper shared by job modules goes to `runner/session.py` only if it is free of the ratings and the job modules (`_has_branch`, `_catch_up`, `_record_refusal`: used by three jobs and `runner/bench.py`); the rest that two jobs share stays in the first job module that has it, and the later ones import it from there (D4 already lets `lead_job` import `developer_job`): `block`, `_check_all`, `_check_results`, `_merged_line`, `_logs_dir`, `waiting_behind`. `block` calls `rate_finished`, so it cannot sit in session, which is below the rating store.
- **D5: unchanged.** `now`, `clock`, `set_activity`, `_notify`, `OPEN_RUNS`, `POLL_S`, `HEARTBEAT_EVERY` are in `runner/session.py`; `fresh_reading`, `_windows_now`, `_passed_over`, `_held_at_the_limit`, `wait_for_room` in `runner/waits.py`; `tests/runner/` patches them there. Patches left on `loop` all name what the scheduler calls (`run_task`, `pre_review`, `handle_escalation`, `run_queued`, `work_queue`, `open_session`, `close_session`, `sync_cards`, `sync_tickets`, `run_bounded`, …). One addition: `_ticket_problems` is called inside the lead job, so after f290-05 it is patched on `lead_job`.
- **D8: unchanged.** Session landed at 1,728 lines, 72 under the cap: f290-04 adds about 45 (three helpers). The five moves take about 3,200 lines from `runner/loop.py`, leaving about 1,600 (under 2,000). `test_waits.py` is small because the waits' tests drive `work_queue` and stay in `test_loop.py` (D6).
- **f290-04 (developer job):** changed. Added `runner/owner.py` and `tests/runner/test_owner.py` (they import `BLOCKED_KIND`, `blocked_text`); `max_diff` 7,000 → 9,000 (about 940 lines of code and about 2,400 of tests, twice); Context now names what stays in loop for f290-08 (`catch_up_plan`, `both_added`), what goes to session, what later jobs import from here, `route_developer`, and the in-function loop imports for `run_lead_task`, `rate_finished`, `current_ratings`. The `_check_context` to `_queue_look` range and the names it lists are where the ticket says.
- **f290-05 (lead job):** changed. `keep_blocked_work` stays in loop (only the scheduler and `runner/requests.py` call it, D3); `_settling` and `_ticket_problems`, `_written_tickets` added to its list; `runner/requests.py` dropped from `files:`; Context says what it imports from developer_job and session, and that `handle_escalation` stays patched on `loop`.
- **f290-06 (rating store):** changed. `current_ratings` and `_bench_game` named (f290-01 left the first); `tests/runner/test_ratings.py` and `tests/runner/test_cli.py` (call `loop.rate_*`, `loop.starting_ratings`) and `runner/lead_job.py` added to `files:`; Context says to replace the in-function loop imports f290-04 and f290-05 leave.
- **f290-07 (review job):** changed. `runner/bench.py` added (imports `_answer_json`, `_merge_files`); `checkpoint_reason` is in session already, so only `_name_checkpoint` and `review_reason` remain to move; Context names its imports (`block` from developer_job, `_written_tickets`, `_repair_ticket` from lead_job, `_record_refusal` from session).
- **f290-08 (planner job):** changed. `max_diff` 6,000 → 8,000; `tests/runner/test_requests.py` added (`loop._plan_branch`); the setup/planner import note corrected (`runner/planner.py` imports neither loop nor session; `MAIN` is `session.MAIN`); the `test_planner.py` patch is already on `session`.
- **Also found:** `_queue_look` has one caller (`_look_at_block`), so it moves with `block`. Not changed: f290-06's `files:` already named `runner/milestone.py`, `runner/cli.py` and `runner/bench.py`.

## As built (f290-08)
- `runner/planner_job.py`: 661 lines (the planner and setup jobs, plan branches, drafts, the auto-merge, where the work stands, naming a card, `setting_up`).
- `tests/runner/test_planner_job.py`: 135 lines (where the work stands, a merged ticket's minutes, `both_added`); the planner and setup tests that drive the queue stay in `tests/runner/test_loop.py` (D6).
- `runner/loop.py`: 1,487 lines, the scheduler only; `tests/runner/test_loop.py`: 7,578.
- `setting_up` moved with `run_setup` (the scheduler imports it from `runner/planner_job.py`); `project_pause`, `project_archived` and `paused_by_you_since` stay (the scheduler and `runner/cli.py`). `_dispatch_tickets` stays (the dry run uses it): `work_stands` imports it inside the function.
- `runner/setup.py` imports `runner.planner` at the top now, and `runner/planner_job.py` imports `runner.setup` at the top: neither path reaches the loop. `factory_dashboard/board.py` imports `ticket_minutes` from `runner/planner_job.py`.
