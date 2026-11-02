# Review: F55, settled threads leave the desk

- **Status:** done, signed off by the owner on 2026-10-08.

## Sign-off sheet

**Expected:** the desk starts clean. Every thread whose plan you already approved, or whose card was merged into another, leaves "Your answers wanted" and Needs you once, and shows under Archived as approved. Nothing still waiting for you is hidden.
**Done when:** on `/planning`, no card whose plan you approved is under "Your answers wanted", and neither are F45 or F47; they are under Archived as approved. A card with a proposal still waiting for you stays on the desk.

### 1. What changed
- At the runner's first start after this landed, a one-off clear-out archived each card thread that was settled already. A thread counts as settled when its card is ready, building, needs sign-off or done (or is gone from main), the lead spoke last, and nothing in the lead's latest reply is still waiting for you. The runner's log line reads "archived the settled threads of …".
- From now on, merging a card into another archives the merged card's thread as approved, right after its "merged into" line (F45 and F47 had come back to the desk that way).
- Archived threads now say why: "approved" when everything was settled, "by you" when you pressed Archive.
- Built together with F31 D1: once you approve every proposal of a reply, the runner adds "Approved by the owner on <date>: …" and archives the thread itself.

### 2. How to test it yourself
1. On your phone, open `/planning`. Under "Your answers wanted", check that none of the cards whose plan you approved today (F17, F19, F22, F23, F25, F26, F28, F30, F32, F33, F41, F42, F48 to F51, F55) are listed, and neither are F45, F47 or F56.
2. Open **Archived**: they're there, each marked "approved".
3. A card whose reply still has something open (an ADR or a replan you haven't answered) is still on the desk.
4. Open one archived thread and send it a message: it comes back to the desk and stays there after the next runner start.

### 3. Left for later
- Backlog (f55-F2): the clear-out is marked done just before it runs, so if it ever failed it wouldn't try again. Unlikely; the fix is to mark it after.
- Rejecting a proposal (F31's other half) stays in f31-01, still ready.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-08, terminal session with you: f55-01 built by the lead with F31 D1 (`7f91225`), after the merge-archive part landed in `53686c5`. No runner session built it, so there's no report in `docs/sessions/`. 2026-10-08 18:14: this review's run, no tickets.
- Lessons:
  - Building F55 with F31 D1 paid off. "Settled" is now one function (`proposal_state`, in `runner/planner.py`) that the desk, the thread page and the runner all read, so they can't disagree.
  - The clear-out's tests only had lead replies without proposals, which never happens in practice. The review added the real case: a plan you approved is archived, and an ADR left unanswered keeps its thread.
  - Lead-built terminal work still reads "0 of 1 merged" below (backlog f41-F3).

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Finish f31-01 (reject), so every proposal can be closed either way from the desk. Then "Your answers wanted" only ever means a real question.
  - F51 (the desk counts what waits on you) builds on the same `proposal_state`. Do it next, while the code is fresh.
  - Counting terminal-built tickets in the report (backlog f41-F3) would stop milestones like this one reading as zero.

### 7. What clogged the factory line
Nothing on this card. It was built in a terminal session and reviewed right after F41's verdict, with no limit waits, failed attempts or stops.

## What was built
- **The clear-out** (`runner/requests.py` `_clear_out`, `runner/metrics.py` `_V12`, `once`): a `once_steps` table records the one-off steps a database has done. A new database starts with F55's marked done; an older one runs it at the first `apply_requests`. It archives (as `approved`, `planning` item resolved) each open non-general thread whose last message is the lead's and whose card is ready, building, needs sign-off, done or gone from main, with every proposal of the latest set settled by `proposal_state` (or a merge whose card has left main).
- **Merges archive** (`_merged`): the duplicate's thread is archived as `approved` after its pointer line.
- **Shared state** (`runner/planner.py` `proposal_state`): moved from the dashboard so the runner uses the same rule. `archived_why` is shown on the Archived list.
- Tests: `test_the_clear_out_archives_settled_threads_once`, `test_a_new_database_owes_no_clear_out` (`tests/runner/test_planner.py`), and the merge test in `tests/runner/test_requests.py`. The ticket listed `test_metrics.py`/`test_requests.py`; the clear-out's tests sit with the archive tests in `test_planner.py` instead, which is fine.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f55-F1 | should-fix | claude | The clear-out's tests never had a lead reply with proposals on a card still on main, so the ticket's first Done when (a ready card whose plan was approved) wasn't exercised, nor "building", nor an ADR left open beside an approved plan | Fixed: `test_the_clear_out_reads_the_owners_approvals_of_the_latest_proposals` |
| f55-F2 | nit | backlog | `metrics.once` commits before `_clear_out` runs; an exception would lose the step for good | `docs/backlog.md` |

Edited existing tests: `test_a_fresh_path_gets_every_table_and_the_latest_version` (schema version 11 → 12, right) and `test_a_merge_proposed_on_the_kept_cards_thread_with_its_plan_goes_in_one_commit`. That test's expectation changed from "F10's reply still waits" to "the thread closes with the approval line", which is F31 D1's intended behaviour, and the new assertion is stricter.

No checkpoint ran (lead-built in a terminal), so there are no checkpoint findings to judge. French: nothing to check. The factory dashboard is English only and no `coucou/locale/` file changed. Gates after the fix: `runner check-all` OK.

Score: 8/10. It is small and correct, and it shares one definition of "settled" with F31. Its tests missed the case it exists for.

## Workflow observations
- A one-off data step is new for the runner. The `once_steps` table makes it cheap, with new databases marked done at creation. Reuse it for later clean-ups rather than adding schema steps that write data.
- As with F41, the review is the only reader of lead-built terminal work. The missed test case is what a checkpoint would have flagged.

<!-- runner report -->
## Numbers

_Written by `uv run runner report f55-dismiss-all-conversations-where-the-related` from the metrics database, which isn't in git: a snapshot. Run it again to refresh; edit outside these markers._

| Result | F55-DISMISS-ALL-CONVERSATIONS-WHERE-THE-RELATED |
|---|---|
| Tickets merged | 0 of 1 |
| First-attempt pass rate | - |
| Local attempts | 0 |
| Escalations, directions, checkpoints | 0, 0, 0 |
| Review rounds | 1 |
| Findings | none |
| Local model | 0 tokens (0 in, 0 out) |
| Claude | $1.24 (248k token-equivalents) |

### Savings from delegating

What Claude would have spent writing the lines the developers merged, against what it spent supporting them: tickets, directions, escalations, and a share of the reviews and checkpoints (f1 D7). API-equivalent dollars.

| Developer | Tickets | Lines | Doing it itself | Supporting | Net |
|---|---|---|---|---|---|
| **All** | 0 | 0 | $0.00 | $0.00 | **$0.00** |

Tokens underneath: doing it itself ≈0 token-equivalents, supporting ≈0.

### By agent

| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |
|---|---|---|---|
| claude-opus | 2 | 248k | $1.24 |

### Trends

| Milestone | Merged | First-attempt | Attempts | Claude | Net savings |
|---|---|---|---|---|---|
| m1 | 5 | 4/5 (80%) | 7 | $1.51 | -$0.63 |
| m2 | 4 | 4/5 (80%) | 6 | $3.45 | -$2.63 |
| m3 | 10 | 10/11 (91%) | 13 | $4.95 | -$1.12 |
| m4 | 11 | 7/11 (64%) | 28 | $1.02 | $12.29 |
| f1 | 48 | 15/22 (68%) | 45 | $83.85 | $33.24 |
| f6-planning-room | 30 | 7/15 (47%) | 32 | $55.75 | -$12.28 |
| bugs | 0 | - | 0 | $0.00 | $0.00 |
| f2 | 12 | 1/3 (33%) | 9 | $39.43 | -$3.00 |
| f3 | 25 | 2/16 (12%) | 50 | $54.52 | -$18.92 |
| f4-always-on | 31 | 10/21 (48%) | 42 | $26.27 | -$4.05 |
| f5-board | 8 | - | 0 | $16.16 | $0.00 |
| f7-factory-fixes | 7 | - | 0 | $12.96 | $0.00 |
| f8-one-queue | 11 | 2/3 (67%) | 5 | $24.14 | $1.20 |
| f9-line-polish | 9 | 4/9 (44%) | 21 | $2.18 | $4.00 |
| f10-crates | 0 | - | 0 | $0.00 | $0.00 |
| f11-test | 0 | - | 0 | $0.50 | $0.00 |
| f12-turn-on-notifications-little-feedback-button | 0 | - | 0 | $5.97 | $0.00 |
| f13-planting-idea-ui-feedback | 0 | - | 0 | $0.52 | $0.00 |
| f14-coming-planted-ideas-not-clickable | 0 | - | 0 | $0.87 | $0.00 |
| f15-reprioritising-tickets | 0 | - | 0 | $0.00 | $0.00 |
| f16-planning-still-says-your-answer-wanted | 0 | - | 0 | $0.42 | $0.00 |
| f17-tighter-running-and-pause-presence-in | 0 | - | 0 | $0.94 | $0.00 |
| f18-arrow-to-reprioririse-queue | 0 | - | 0 | $0.00 | $0.00 |
| f19-will-i-need-to-refresh-planning | 0 | - | 0 | $0.65 | $0.00 |
| f20-data-safety | 2 | - | 0 | $5.29 | $0.00 |
| f21-lead-briefs | 0 | - | 0 | $0.00 | $0.00 |
| f22-move-archive-button-on-planning-desk | 0 | - | 0 | $1.02 | $0.00 |
| f23-when-i-click-comment-on-the | 0 | - | 0 | $1.00 | $0.00 |
| f24-bug-when-i-answer-a-ticket | 0 | - | 0 | $0.45 | $0.00 |
| f25-whenever-i-plant-something-does-it | 0 | - | 0 | $1.90 | $0.00 |
| f26-i-want-to-see-numbers-next | 0 | - | 0 | $0.53 | $0.00 |
| f27-when-i-pause-the-factory-i | 0 | - | 0 | $6.55 | $0.00 |
| f28-the-first-time-i-clicked-on | 0 | - | 0 | $0.65 | $0.00 |
| f29 | 0 | - | 0 | $1.09 | $0.00 |
| f29-the-top-was-saying-resuming-but | 0 | - | 0 | $0.62 | $0.00 |
| f30-on-conversations-i-want-to-the | 0 | - | 0 | $0.59 | $0.00 |
| f31-when-i-click-on-approve-plan | 1 | - | 0 | $3.84 | $0.00 |
| f32-the-5-hour-lead-s-window | 0 | - | 0 | $0.59 | $0.00 |
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
| f48-the-didnt-go-through-cards-try | 0 | - | 0 | $1.64 | $0.00 |
| f49-don-t-ask-me-to-merge | 0 | - | 0 | $0.87 | $0.00 |
| f50-the-data-safety-review-it-asks | 0 | - | 0 | $1.61 | $0.00 |
| f51-when-a-plan-depends-on-an | 0 | - | 0 | $1.16 | $0.00 |
| f52-not-a-fan-of-the-layout | 0 | - | 0 | $0.62 | $0.00 |
| f53-why-is-milestone-diff-review-waiting | 0 | - | 0 | $1.03 | $0.00 |
| f54-the-reprioritise-up-down-arrows-do | 0 | - | 0 | $1.01 | $0.00 |
| f55-dismiss-all-conversations-where-the-related | 0 | - | 0 | $1.24 | $0.00 |
| f56-dismiss-all-conversations-where-the-work | 0 | - | 0 | $0.58 | $0.00 |
| f57-reprioritise-for-me-while-i-dont | 0 | - | 0 | $0.92 | $0.00 |
| f58-when-i-ask-the-lead-a | 0 | - | 0 | $0.60 | $0.00 |
| f59-periodic-review-of-the-factory | 0 | - | 0 | $0.00 | $0.00 |
| f60-suggest-improvements-to-ai-workflow | 0 | - | 0 | $0.00 | $0.00 |
| f61-on-claude-usage-page-there-is | 0 | - | 0 | $0.00 | $0.00 |
| f62-claude-opus-review-on-overview-does | 0 | - | 0 | $0.00 | $0.00 |
| m0 | 0 | - | 0 | $0.00 | $0.00 |
| **All** | 214 | 66/121 (55%) | 258 | $384.01 | $8.10 |
<!-- /runner report -->
