# Review: F53, a review waiting for Claude doesn't stop the line

- **Status:** done, signed off by the owner on 2026-10-13.

## Sign-off sheet

**Expected:** a review Claude can't take now waits in the queue, like a parked checkpoint, and developer tickets run meanwhile. It goes first again as soon as Claude has room.
**Done when:** with Claude over its 75% (switch off), a due review parks until the window resets, the console and the queue say so, and the next developer ticket starts at once; no e2e run for a parked review; after the reset the review is the next pick and starts at the round it was at; the 5-hour switch ends the wait at the next pick; a review parked between rounds re-reads only its own milestone's fixes.

### 1. What changed
- When a milestone's review is due and Claude has no room (the 5-hour window over 75% with the switch off, or a real limit), `runner run` no longer sleeps. The console says "⏸ the review of f20-data-safety waits for Claude · resumes 12:41", and the next developer ticket starts straight away.
- The check comes before the end-to-end tests, so a review that parks doesn't run them for nothing.
- Once the window resets, or as soon as you turn the 5-hour switch on, the review is the next pick, before any ticket. A review parked before its round 2 starts at round 2.
- With no ticket left to run, the runner sleeps until the review's reset and then reviews, instead of ending the run.
- A review that parked between rounds is told which merges are its own fixes, so it doesn't read other milestones' work as its own.
- `uv run runner milestone <key>` is unchanged: it has no queue to go back to, so its review still waits for the reset.
- Not there yet: on the factory line and under "Next in line", a parked review still shows as number 1 with nothing saying it waits (finding F2, ticket `f53-02-parked-review-crate`). The overview's job row above it does say "waits until 12:41".

### 2. How to test it yourself
It only shows when Claude is over 75% of its 5-hour window while a review is due, so the easiest check is the next time that happens:
1. Leave the 5-hour switch off and let `uv run runner run` reach a due review with Claude's 5-hour window above 75%.
2. In the console, look for "the review of … waits for Claude · resumes HH:MM", followed at once by a developer ticket starting (no "e2e tests" line in between).
3. On your phone, open the overview: under "Next in line" the row "Review: … · waits until HH:MM" is there, and a ticket is being worked on at the top.
4. Turn the 5-hour switch on from the dashboard. After the ticket under way finishes, the review starts next.
5. To see it without waiting for that day: `uv run pytest -q tests/runner/test_milestone.py -k parked_between_rounds` plays the whole story (round 1, park, another milestone's ticket, round 2, verdict).

### 3. Left for later
- `f53-02-parked-review-crate` (ready, a developer): the parked review's crate on the line and its "Next in line" row say "waits for Claude's reset at HH:MM" and go behind the tickets that can run.
- Backlog (f53-F3): the list of fix merges a parked review gets leaves out its own last round's commit, where the review's direct fixes and new tickets are.

### 4. Decisions waiting for you
None. D2 (no Copilot stand-in for the review) and D3 (one review per milestone) were settled in the plan and nothing in the build argues against them.

### 5. How the work went
- 2026-10-13 00:12 ([session](../sessions/2026-10-13-0012.md)): `f53-01-park-the-review` merged at its first attempt, a headless lead job (`runner/` is protected). It was the last of 6 merges in a 430-minute session whose 10.4M local tokens went to other milestones' tickets; none were spent on F53. The runner stopped after it for a fresh process, as it does when `runner/` changes.
- 2026-10-13 07:22: this review, round 1. One test restored by the review, one developer ticket filed.
- Lessons:
  - The ticket said which two tests to replace. One of them was the only test of the 5-hour switch ending a `runner milestone` wait, which is still live code. "Replace" in a ticket should say whether the old behaviour is gone or only moved; the review put that test back.
  - The plan's Done when said "the console and the queue say…". The ticket carried only the console half, so the line's crate was left behind. A Done-when line that names two places needs both in a ticket.
  - The headline test plays the real incident end to end through `runner run` (round 1, park, another milestone's merge, round 2, verdict) and asserts that nothing slept. That is the right shape for runner fixes: the test is the log from the day it went wrong.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Run `f53-02-parked-review-crate`, so the line shows what the console already says.
  - The session that built this lost three attempts each on f5-08 and f3-08 to "no edit after 10 min". Its own suggestion is worth a lead ticket: after two attempts that both stopped with no edit, skip the direction and escalate.
  - `check-all --task` takes over 10 minutes and times out for developers and the lead alike. Let it print its quick gates (ruff, format, mypy) before the tests start, so a timeout still shows them.

### 7. What clogged the factory line
- **The clog this milestone removes:** on 2026-10-08 the runner slept 3 h 30 (09:10 to 12:41) waiting for Claude with about 40 developer tickets ready. From now on that time goes to developer tickets.
- **F53 itself:** one attempt, no limit wait, no stop for you. The card was planted on 2026-10-08 and its ticket merged on 2026-10-13: it waited its turn behind F5 and F6 work, which is the priority order you set, not a clog.
- **The session around it** (not F53's tickets): six attempts on two tickets stopped at "no edit after 10 min" before the lead took them over, about an hour of local time with nothing merged. The fix is the lead ticket suggested above.
- I couldn't read hours from the metrics database in this job (a headless review has no query command); the figures above are from the session report and the plan's notes. Fix: give `runner report` a "where the hours went" block, so reviews quote it like the other numbers (added to the backlog).

## What was built
- **Parking** (`runner/loop.py`): `park_review` asks `claude_hold` and, when Claude can't take the review, parks its row through `_park_support`, the checkpoint's path. `work_queue` calls it when the pick is a review and carries on with the next pick. `_parked_ahead` counts a parked review row, so the queue sleeps to its reset when nothing else can run, and a review parked for a real limit keeps lead work back as a parked checkpoint does (one held only by your 25% doesn't).
- **The rounds** (`runner/milestone.py`): `review_milestone(..., park=True)` (from `run_due_review`) checks before each round, before e2e, and returns `PARKED` without recording a stop, finishing the row or writing metrics. Without `park` (`runner milestone`) it calls `wait_for_room` at the same place, which also moves that wait in front of the e2e run. `_last_round` finds where a resumed review left off from its last round's commit (a restarted review used to fall back to the whole milestone diff). `_fix_scope` names the milestone's own fix merges when another milestone's ticket merged in between.
- **The command** (`runner/cli.py`): `_review` returns to the queue on `PARKED`, with no verdict.
- **Tests:** five in `tests/runner/test_loop.py` (park and go on, sleep to the reset with nothing left, the switch, limits ahead) and three in `tests/runner/test_milestone.py` (`runner milestone` still waits, the whole parked-between-rounds story through `cli.main(["run"])`, the scope's two forms).

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | `test_the_5_hour_switch_turned_on_during_the_reviews_wait_ends_it` was replaced, but `wait_for_room` still runs under `runner milestone` and nothing else tests that the switch ends its wait (the 60-second poll) | Fixed: restored as `test_the_5_hour_switch_turned_on_during_a_named_milestones_wait_ends_it` |
| F2 | should-fix | local | The dashboard doesn't know a review is parked: `_due_reviews` (`factory_dashboard/line.py`) still puts its crate first with `"waits": []`, and "Next in line" lists it as number 1 "a batch". A review parked between rounds (status `review`) has no crate at all. The plan's Done when asks for the queue to say it waits | Ticket `f53-02-parked-review-crate` |
| F3 | nit | backlog | When other milestones merged in between, `_fix_scope` lists only `Task:` merges, so the review's own last-round commit (its direct fixes, the tickets it wrote) is no longer in what round 2 is pointed at | `docs/backlog.md` |

Edited existing tests, each read:
- `test_a_review_at_80_percent_waits_for_the_reset_with_the_switch_off` became `…parks_and_a_developer_ticket_runs_meanwhile`: the old expectation (the clock moves past the reset) is the behaviour F53 removes. The new one is stricter: a ticket ran, nothing slept, the row's `not_before`, the console line, no stop recorded, and the review picked after the reset.
- `test_the_5_hour_switch_turned_on_during_the_reviews_wait_ends_it` became `…while_the_review_is_parked_makes_it_the_next_pick`: right for `runner run`, but it dropped the `wait_for_room` case (F1).
- `test_a_due_review_diffs_from_the_plans_commit` and `test_a_replanned_milestones_review_diffs_from_its_first_merge`: their fakes take the new `park` argument, and the first asserts it is set. Nothing weakened.

No checkpoint ran on this ticket (a lead ticket), so there are no checkpoint findings to judge. French: nothing to check, no user-facing string and no `coucou/locale/` file changed. Screenshots: no new screen. After the fix, `uv run pytest -q tests/unit tests/integration tests/runner` gave 1805 passed, 1 skipped and 1 failed: the ticket pre-flight, on two bare file names in the new ticket. With its paths corrected `tests/runner/test_tasks.py` passes (120 passed); the full run wasn't repeated after that one-ticket edit. Ruff is clean on the edited test file.

Score: 8/10. The runner side is correct and follows the checkpoint's path instead of adding one; the tests replay the real incident. It lost one test of code that still runs, and left the dashboard half of a Done-when line undone.

Stop reason: none; round 2 follows the fix ticket.

## Factory
- **The flow:** one lead ticket, one attempt, no stop, no park, no intervention from you. The runner restarted after the merge, as it must when `runner/` changes.
- **Models:** Claude Opus only; see the numbers below. No developer work, so "Known range" in `docs/agents/lead.md` has nothing new.
- **What to change:**
  - F2 goes to a developer although its tests live in `tests/factory_dashboard/test_line.py`, which the same session showed Qwen can't read through (f3-08). The ticket names one test to copy in each file and says not to read the rest. If it stops twice with no edit, the lead takes it without a direction.
  - A lead ticket's work gets no checkpoint, so its review is its only reader (as F41 and F55 noted). F1 is what a checkpoint given the ticket's replaced tests would have asked about.

## Workflow observations
- This review ran under the change it reviews: had Claude been over 75% at 07:22, it would have parked and the line gone on.
- `git diff <start>..main` was the right scope here because the start tag was one commit before the ticket's merge. `_plan_commit` (the parent of the first `Task:` merge) keeps that true for cards planted days before they are built.

<!-- runner report -->
## Numbers

_Written by `uv run runner report f53-why-is-milestone-diff-review-waiting` from the metrics database, which isn't in git: a snapshot. Run it again to refresh; edit outside these markers._

| Result | F53-WHY-IS-MILESTONE-DIFF-REVIEW-WAITING |
|---|---|
| Tickets merged | 1 of 1 |
| First-attempt pass rate | - |
| Local attempts | 0 |
| Escalations, directions, checkpoints | 0, 0, 0 |
| Review rounds | 1 |
| Findings | none |
| Local model | 0 tokens (0 in, 0 out) |
| Claude | $8.84 (1.0M token-equivalents) |

### Savings from delegating

What Claude would have spent writing the lines the developers merged, against what it spent supporting them: tickets, directions, escalations, and a share of the reviews and checkpoints (f1 D7). API-equivalent dollars.

| Developer | Tickets | Lines | Doing it itself | Supporting | Net |
|---|---|---|---|---|---|
| **All** | 0 | 0 | $0.00 | $0.00 | **$0.00** |

Tokens underneath: doing it itself ≈0 token-equivalents, supporting ≈0.

### By agent

| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |
|---|---|---|---|
| claude-opus | 5 | 1.0M | $8.84 |

### Trends

| Milestone | Merged | First-attempt | Attempts | Claude | Net savings |
|---|---|---|---|---|---|
| m1 | 5 | 4/5 (80%) | 7 | $1.51 | -$0.56 |
| m2 | 4 | 4/5 (80%) | 6 | $3.45 | -$2.55 |
| m3 | 10 | 10/11 (91%) | 13 | $4.95 | -$0.92 |
| m4 | 11 | 7/11 (64%) | 28 | $1.02 | $12.23 |
| f1 | 48 | 15/22 (68%) | 45 | $83.85 | $33.74 |
| f6-planning-room | 30 | 7/15 (47%) | 32 | $55.75 | -$11.60 |
| bugs | 0 | - | 0 | $0.00 | $0.00 |
| f2 | 12 | 1/3 (33%) | 9 | $39.43 | -$3.07 |
| f3 | 25 | 2/16 (12%) | 50 | $54.52 | -$18.70 |
| f4-always-on | 31 | 10/21 (48%) | 42 | $26.27 | -$3.71 |
| f5-board | 15 | 1/3 (33%) | 7 | $32.33 | -$3.55 |
| f7-factory-fixes | 7 | - | 0 | $12.96 | $0.00 |
| f8-one-queue | 14 | 2/6 (33%) | 14 | $32.19 | -$1.08 |
| f9-line-polish | 31 | 16/32 (50%) | 67 | $11.38 | $10.34 |
| f10-crates | 0 | - | 0 | $0.00 | $0.00 |
| f11-test | 0 | - | 0 | $0.50 | $0.00 |
| f12-turn-on-notifications-little-feedback-button | 2 | 2/2 (100%) | 2 | $11.80 | $0.21 |
| f13-planting-idea-ui-feedback | 0 | 0/1 (0%) | 3 | $2.46 | -$1.94 |
| f14-coming-planted-ideas-not-clickable | 0 | - | 0 | $0.87 | $0.00 |
| f15-reprioritising-tickets | 0 | - | 0 | $0.00 | $0.00 |
| f16-planning-still-says-your-answer-wanted | 0 | - | 0 | $0.42 | $0.00 |
| f17-tighter-running-and-pause-presence-in | 0 | 0/1 (0%) | 3 | $3.15 | -$2.21 |
| f18-arrow-to-reprioririse-queue | 0 | - | 0 | $0.00 | $0.00 |
| f19-will-i-need-to-refresh-planning | 0 | - | 0 | $0.65 | $0.00 |
| f20-data-safety | 2 | - | 0 | $5.29 | $0.00 |
| f21-lead-briefs | 0 | - | 0 | $4.96 | $0.00 |
| f22-move-archive-button-on-planning-desk | 0 | - | 0 | $1.02 | $0.00 |
| f23-when-i-click-comment-on-the | 0 | - | 0 | $1.00 | $0.00 |
| f24-bug-when-i-answer-a-ticket | 0 | - | 0 | $0.45 | $0.00 |
| f25-whenever-i-plant-something-does-it | 0 | - | 0 | $1.90 | $0.00 |
| f26-i-want-to-see-numbers-next | 1 | 1/1 (100%) | 1 | $3.01 | -$0.47 |
| f27-when-i-pause-the-factory-i | 0 | - | 0 | $6.55 | $0.00 |
| f28-the-first-time-i-clicked-on | 0 | - | 0 | $0.65 | $0.00 |
| f29 | 0 | - | 0 | $1.09 | $0.00 |
| f29-the-top-was-saying-resuming-but | 0 | - | 0 | $0.62 | $0.00 |
| f30-on-conversations-i-want-to-the | 0 | - | 0 | $0.59 | $0.00 |
| f31-when-i-click-on-approve-plan | 1 | - | 0 | $6.98 | $0.00 |
| f32-the-5-hour-lead-s-window | 0 | 0/1 (0%) | 3 | $1.64 | -$1.06 |
| f33-overview-now-check-all-how-long | 0 | - | 0 | $0.73 | $0.00 |
| f34-planner-tasks-cannot-be-paused-but | 0 | - | 0 | $0.39 | $0.00 |
| f35-when-i-m-reviewing-what-s | 0 | - | 0 | $0.00 | $0.00 |
| f36-whenever-the-planner-is-planning-and | 0 | - | 0 | $0.00 | $0.00 |
| f37-in-planning-mode-it-tends-to | 0 | - | 0 | $0.00 | $0.00 |
| f38-the-refresh-prompt-causes-layout-shifting | 0 | - | 0 | $0.00 | $0.00 |
| f39-limits-on-tickets-per-milestone | 0 | - | 0 | $0.00 | $0.00 |
| f40-need-back-up-code-asap | 0 | - | 0 | $0.00 | $0.00 |
| f41-i-find-that-on-conversations-there | 0 | - | 0 | $1.92 | $0.00 |
| f42-the-space-for-me-to-scroll | 0 | - | 0 | $0.87 | $0.00 |
| f43-what-happens-when-a-proposal-has | 0 | - | 0 | $1.75 | $0.00 |
| f44 | 0 | - | 0 | $0.72 | $0.00 |
| f44-in-proposal-i-don-t-need | 0 | - | 0 | $0.39 | $0.00 |
| f45-when-i-approve-a-plan-it | 0 | - | 0 | $0.27 | $0.00 |
| f46-the-dismiss-cards-that-didn-t | 0 | - | 0 | $5.28 | $0.00 |
| f47-when-i-a-pprove-a-plan | 0 | - | 0 | $0.28 | $0.00 |
| f48-the-didnt-go-through-cards-try | 1 | 1/1 (100%) | 1 | $5.89 | -$0.35 |
| f49-don-t-ask-me-to-merge | 0 | - | 0 | $0.87 | $0.00 |
| f50-the-data-safety-review-it-asks | 0 | - | 0 | $3.17 | $0.00 |
| f51-when-a-plan-depends-on-an | 0 | - | 0 | $1.16 | $0.00 |
| f52-not-a-fan-of-the-layout | 0 | - | 0 | $0.62 | $0.00 |
| f53-why-is-milestone-diff-review-waiting | 1 | - | 0 | $8.84 | $0.00 |
| f54-the-reprioritise-up-down-arrows-do | 0 | - | 0 | $3.14 | $0.00 |
| f55-dismiss-all-conversations-where-the-related | 0 | - | 0 | $2.17 | $0.00 |
| f56-dismiss-all-conversations-where-the-work | 0 | - | 0 | $0.58 | $0.00 |
| f57-reprioritise-for-me-while-i-dont | 0 | - | 0 | $0.92 | $0.00 |
| f58-when-i-ask-the-lead-a | 0 | - | 0 | $0.60 | $0.00 |
| f59-periodic-review-of-the-factory | 0 | - | 0 | $0.00 | $0.00 |
| f60-suggest-improvements-to-ai-workflow | 0 | - | 0 | $0.00 | $0.00 |
| f61-on-claude-usage-page-there-is | 0 | - | 0 | $0.00 | $0.00 |
| f62-claude-opus-review-on-overview-does | 0 | - | 0 | $0.00 | $0.00 |
| f63-i-want-to-see-cards-in | 0 | - | 0 | $1.28 | $0.00 |
| f63-there-are-items-finished-to-talk | 0 | - | 0 | $0.44 | $0.00 |
| f64-i-like-to-see-the-list | 0 | - | 0 | $1.50 | $0.00 |
| f64-it-is-still-the-case-that | 0 | - | 0 | $0.45 | $0.00 |
| f64-your-review-in-planning-doesn-t | 0 | - | 0 | $0.88 | $0.00 |
| f65-the-lead-is-reviewing-stuff-but | 0 | - | 0 | $0.37 | $0.00 |
| f65-what-happens-if-i-comment-on | 0 | - | 0 | $1.80 | $0.00 |
| f66-the-number-of-key-points-under | 0 | - | 0 | $0.00 | $0.00 |
| f67-in-proposals-sometimes-i-see-d1 | 0 | - | 0 | $0.97 | $0.00 |
| f68-i-want-the-factory-to-be | 0 | - | 0 | $2.10 | $0.00 |
| f69-i-want-a-button-to-switch | 0 | - | 0 | $0.60 | $0.00 |
| f70-i-wonder-how-marketable-this-factory | 0 | - | 0 | $0.63 | $0.00 |
| f71-i-suspect-we-might-need-to | 0 | - | 0 | $8.02 | $0.00 |
| f72-i-really-like-the-mock-up | 0 | - | 0 | $0.53 | $0.00 |
| f73-do-i-need-to-accecpt-both | 0 | - | 0 | $0.40 | $0.00 |
| f73-i-want-to-be-able-to | 0 | - | 0 | $0.82 | $0.00 |
| f74-when-i-reply-to-a-your | 0 | - | 0 | $0.70 | $0.00 |
| f75-i-believe-right-now-when-a | 0 | - | 0 | $0.69 | $0.00 |
| f76-the-refresh-popup-does-layout-shifting | 0 | - | 0 | $0.00 | $0.00 |
| f77-the-bars-in-the-agent-allowance | 0 | - | 0 | $0.00 | $0.00 |
| f78-remove-planning-may-go-past-the | 0 | - | 0 | $0.00 | $0.00 |
| f79-when-a-task-times-out-on | 0 | - | 0 | $1.65 | $0.00 |
| f80-developer-rating-could-be-more-tailored | 0 | - | 0 | $0.00 | $0.00 |
| f81-assess-the-current-ui-state-of | 0 | - | 0 | $0.00 | $0.00 |
| f82-the-plant-idea-text-box-is | 0 | - | 0 | $0.00 | $0.00 |
| f83-is-the-planning-conversation-efficient-atm | 0 | - | 0 | $0.00 | $0.00 |
| f84-when-the-planner-is-replying-to | 0 | - | 0 | $0.00 | $0.00 |
| f85-when-i-sign-off-a-task | 0 | - | 0 | $0.00 | $0.00 |
| f86-idea-tracking-time-the-human-spent | 0 | - | 0 | $0.00 | $0.00 |
| f87-i-want-a-daily-report-of | 0 | - | 0 | $0.00 | $0.00 |
| f88-add-to-lead-memory-that-new | 0 | - | 0 | $0.52 | $0.00 |
| f89-does-allowance-refresh-at-the-beginning | 0 | - | 0 | $0.00 | $0.00 |
| f90-editing-seeds-that-i-ve-planted | 0 | - | 0 | $0.88 | $0.00 |
| f91-the-proposals-and-mockups-and-adrs | 0 | - | 0 | $0.00 | $0.00 |
| f92-claude-per-milestone-on-overview-is | 0 | - | 0 | $0.00 | $0.00 |
| f93-is-no-edit-after-10-minutes | 0 | - | 0 | $0.00 | $0.00 |
| f94-opus-f9-25-seeds-and-planting | 0 | - | 0 | $0.88 | $0.00 |
| f95-overview-currently-says-i-have-2 | 0 | - | 0 | $6.27 | $0.00 |
| f96-i-want-threads-in-your-answers | 0 | - | 0 | $0.00 | $0.00 |
| f97-given-that-the-planning-board-has | 0 | - | 0 | $0.00 | $0.00 |
| f98-if-i-have-slow-internet-and | 0 | - | 0 | $0.00 | $0.00 |
| f99-when-a-proposal-has-bundled-things | 0 | - | 0 | $0.00 | $0.00 |
| f100-if-i-replied-to-a-conversation | 0 | - | 0 | $0.00 | $0.00 |
| f101-uv-runner-run-command-stopped-when | 0 | - | 0 | $0.00 | $0.00 |
| f102-i-want-conversations-that-don-t | 0 | - | 0 | $0.00 | $0.00 |
| f103-the-number-of-things-in-planning | 0 | - | 0 | $0.00 | $0.00 |
| f104-mockups-act-like-i-can-interact | 0 | - | 0 | $1.01 | $0.00 |
| f105-do-planted-ideas-disappear-if-the | 0 | - | 0 | $0.83 | $0.00 |
| f105-in-a-group-proposal-where-there | 0 | - | 0 | $0.34 | $0.00 |
| f106-where-do-blocked-tickets-go-for | 0 | - | 0 | $3.11 | $0.00 |
| f107 | 0 | - | 0 | $1.66 | $0.00 |
| f107-in-a-recent-conversation-about-blocked | 0 | - | 0 | $0.80 | $0.00 |
| f107-overview-page-says-i-have-this | 0 | - | 0 | $1.30 | $0.00 |
| f108-in-your-answers-wanted-i-see | 0 | - | 0 | $0.93 | $0.00 |
| f109-when-plans-get-merged-i-need | 0 | - | 0 | $1.03 | $0.00 |
| m0 | 0 | - | 0 | $0.00 | $0.00 |
| **All** | 251 | 83/157 (53%) | 333 | $499.13 | $4.76 |
<!-- /runner report -->
