# Review: F8, one visible queue

- **Status:** round 1 done, waiting for the owner's sign-off.
- **Stop reason:** none. Round 1 found 4 should-fix points and 3 nits. The lead fixed 3 should-fix points itself (two in protected runner code, one 3-line dashboard crash). The fourth, a missing test, is ticket f8-13 for a developer. The nits are in the backlog. No ADR is needed.

## Sign-off sheet

### 1. What changed
- **Two switches on the Overview, below Now**, beside Claude's week and 5-hour meters: "Let the factory use the week's reserve" and "Let the factory use your 25% of the 5-hour window". Each says "off" or "on until Sat 09:30". A tap shows at once with a dashed orange edge ("asked: on") until the runner takes it. The panel now refreshes every 5 s with the rest of the live page.
- **The console asks nothing any more.** Before, it asked y/N for the reserve. Now `uv run runner reserve week on` (or `five-hour`, `off`) and `uv run runner run --use-reserve` do the same as the switches.
- **A switch turns itself off after 24 hours.** Needs you then asks "Turn … on again for 24 h?".
- **Next in line shows every job, not only tickets:** a checkpoint, an escalation, a direction, a review or a planning reply, each with its reason ("Checkpoint: f9 · after f8-07 and f9-04 merged"), and "waits until Mon 5 Oct 17:00" when it is parked.
- **`uv run runner run --dry-run`** prints that same list in run order, each job with why it is there and what it waits for.
- **Claude checks again what a stand-in checked.** When Copilot stood in for a checkpoint, one queued Claude checkpoint now re-checks those merges once Claude's window allows.
- **A stand-in's fix tickets are fewer and doable.** One ticket per merged ticket and kind of fix. A weak test becomes a developer's tests-only ticket, not a lead job.
- Nothing about what runs changed: the same caps, attempts, checkpoints and reviews.

### 2. How to test it yourself
1. On your phone, open the Overview and scroll below Now. Each Claude meter should have its switch, saying "off" with a **Turn on** button. Copilot's and Ollama's meters have none.
2. Tap **Turn on** under the week's meter. The switch should get a dashed orange edge and say "asked: on". After the runner's next pick, it should say "on until" tomorrow at this time, with **Turn off**.
3. Tap **Turn off**. It should go back to "off" after the next pick.
4. On the laptop, run `uv run runner run --dry-run`. It should list the queued jobs and the ready tickets in order, with `->` on the next one.
5. When a checkpoint is queued (after a few developer merges), Next in line should show "Checkpoint: …" with its reason, above the tickets.
6. Leave a switch on for a day: it should turn off by itself, and Needs you should ask whether to turn it on again.

### 3. Left for later
- Ticket **f8-13** (a developer's tests-only ticket): a test that a queued job whose job is running stays out of the queue.
- Three nits in [`docs/backlog.md`](../backlog.md): the dry run words Claude's waits differently from the live pick (F4); the queued jobs don't say "paused by you" (F5); an old ticket, `tasks/later/f9-12`, should be deleted (F6).
- From F8's own tickets: f9-20 (the queue says "0 tickets waiting. Drain it with None" when only jobs are queued) is ready in F9.

### 4. Decisions waiting for you
- None.

### 5. How the work went
- 2026-10-05 01:33 → 01:46 ([0133](../sessions/2026-10-05-0133.md), [0146](../sessions/2026-10-05-0146.md)): f8-01 (the table) and f8-02 (the picker), the lead's, both first time.
- 2026-10-06 09:14 → 10:25 ([0914](../sessions/2026-10-06-0914.md), [1025](../sessions/2026-10-06-1025.md)): f8-03 (the loop runs what the picker returns) and f8-04 (the switches), the lead's, first time.
- 2026-10-06 13:42 ([1342](../sessions/2026-10-06-1342.md)), 146 min: f8-05 (replan) and f8-08 (Claude re-checks a stand-in) by the lead. f8-07 (queue view) took Qwen 3 attempts: twice it read 10 minutes without an edit; 4.8M local tokens.
- 2026-10-06 16:08 → 16:33 ([1608](../sessions/2026-10-06-1608.md), [1633](../sessions/2026-10-06-1633.md)): f8-09 (stand-in fix tickets) and f8-10 (the `reserve` request kind), the lead's.
- 2026-10-06 17:12 ([1712](../sessions/2026-10-06-1712.md)): Qwen fixed both stand-in findings on f8-07 (f8-11, f8-12) first time.
- 2026-10-08 23:04 ([2304](../sessions/2026-10-08-2304.md)), 105 min: f8-06 (the switch buttons). Qwen failed 3 times (no edit twice, then a timeout; 7.3M local tokens). Its branch had rewritten its own test to agree with a wrong subject. Opus reset it and built it.
- **Lessons:**
  - Lead tickets on the runner went through first time, 8 of 8. The developer tickets that went well were the small fixes (f8-11, f8-12). The two page tickets (f8-06, f8-07) cost 6 attempts and an escalation.
  - A developer bent its test to its code (f8-06). That is now part of developer.md note 12. The list was at 16 notes, over its limit of 15, so note 16 was merged into note 12.
  - A checkpoint files its findings under its own milestone, so F8's review saw none of the four found on F8's work. Fixed in this review (F7): from now on a finding goes under the milestone of the ticket at fault.

### 6. What next
- **Factory:**
  - Run **F9's polish tickets and f9-20** next. They tidy the queue F8 just filled.
  - **Stop sending Qwen page tickets that touch the live partial.** f8-06 and f8-07 had to read `overview.py`, `line.py` and the runner's state, and Qwen read for 10 minutes without an edit three times out of five. Write such a ticket as one template change on a lead-written function, or give it to the lead. It cost $3.03 to support $1.78 of work here.
  - **ADR 23 (parallel lanes)** is still the next big gain. The one queue gives it the single picker it needed.
- **Product:** on hold, as you asked (2026-10-04).

## What was built
- `work_queue` table (`_V8`) with `queue_job`, `open_jobs` and `finish_queued` (f8-01).
- `runner/dispatch.py`: a pure `pick`/`plan` over the queued jobs and tickets, with reasons. It drives `--dry-run`, the loop's choice between kinds of job, the pause hold and the Overview's order (f8-02, f8-03).
- Support jobs (checkpoint, escalation, direction, review, planner) are queue rows. A parked one waits on its row's `not_before`, and what it needs to restart is in `state.json`'s `queued` (f8-03, D3).
- Two reserve switches in `state.json`'s `switches`, each on for 24 hours, with the `reserve` request, `runner reserve` and `--use-reserve`. A lapsed switch raises a Needs-you item (f8-04, f8-10).
- Claude's re-check of a stand-in's merges, as one queued checkpoint (f8-08). Fix tickets per merged ticket and kind, with `tests_only` tickets and their gate (f8-09).
- The switches on the Overview, which refresh live (f8-06). Queued jobs in Next in line (f8-07, f8-11, f8-12).

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | lead | Claude's re-check dropped any finding on a ticket and file the stand-in had flagged (`checkpoint`, f8-08), so a new problem in that file went unrecorded | Fixed: every finding is recorded, since the prompt already names what the stand-in filed. The test has the re-check find a new problem in the stand-in's file. |
| F2 | should-fix | lead | `queued_jobs` crashed the Overview and `/live` (500) for a project with no row yet (f8-07) | Fixed: nothing queued; new test. Both checkpoints after f8-07 missed it. |
| F7 | should-fix | lead | Checkpoint findings went under the checkpoint's milestone (F9's here), so F8's report and review had none | Fixed: `record_findings(by_ticket=True)` for the checkpoint, its stand-in and its shadow; new test. |
| F3 | should-fix | developer | No test that a queued job with a running job stays out of the queue (f8-07) | Ticket f8-13 (tests only). Missed by both checkpoints. |
| F4 | nit | backlog | The dry run plans with Claude's windows; the live pick lets each job check them itself | backlog |
| F5 | nit | backlog | The queued jobs don't say "paused by you" while paused | backlog |
| F6 | nit | backlog | `tasks/later/f9-12` survived its fold into f9-11 | backlog |

- **Tests the developers edited:**
  - f8-07 only added tests, but they were weak: one asserted only `len(jobs) >= 1`. f8-12 (from the stand-in) fixed them.
  - f8-11's test checks the queue's text when it has jobs but no tickets. Its wording bug is f9-20.
  - f8-06's own test bending was never merged: Opus rewrote the branch.
- **French:** no user-facing strings for Mum in F8. The factory dashboard is English (ADR 00 A2).
- **Checkpoints:** the runner reports none keyed to F8. The stand-in (Copilot) and Claude's re-check after f8-07 filed 3 findings, plus 1 on f8-11 (f9-20). All were real, but they were filed under F9's key (F7), so they weren't judged here. Both checkpoints missed F2 and F3.
- **Score:** 7/10. The core is clean and well tested: one pure picker, and rows that park and resume. The dashboard half needed an escalation, and three real defects reached the review.

## Factory
- **Flow:** 12 merged. The lead's tickets went through in short sessions with no stop. Each lead ticket on `runner/` ended its session with "the runner needs a fresh process", as designed.
- **What clogged the line:** about 50 minutes of Qwen reading without an edit on f8-07, then 105 minutes on f8-06 (two 10-minute stalls and one timeout), 12M local tokens on two page tickets. f8-06 also waited two days on its dependencies (f9-17 and the dials). The fix: route page tickets that touch the live partial to the lead, or split them to one template on a lead-written function (lead.md, Known range).
- **Cost:** $27.65 of Claude. Net savings from delegating were −$1.25: supporting Qwen cost more than writing its four tickets.
- **Stop reason:** none.


_Written by `uv run runner report f8-one-queue` from the metrics database, which isn't in git: a snapshot. Run it again to refresh; edit outside these markers._

| Result | F8-ONE-QUEUE |
|---|---|
| Tickets merged | 12 of 12 |
| First-attempt pass rate | 2/4 (50%) |
| Local attempts | 8 |
| Escalations, directions, checkpoints | 1, 2, 0 |
| Review rounds | 1 |
| Findings | none |
| Local model | 13.5M tokens (13,456,793 in, 69,393 out) |
| Claude | $27.65 (6.3M token-equivalents) |

### Savings from delegating

What Claude would have spent writing the lines the developers merged, against what it spent supporting them: tickets, directions, escalations, and a share of the reviews and checkpoints (f1 D7). API-equivalent dollars.

| Developer | Tickets | Lines | Doing it itself | Supporting | Net |
|---|---|---|---|---|---|
| **All** | 4 | 215 | $1.78 | $3.03 | **-$1.25** |
| local-qwen3.6-35b-a3b | 4 | 215 | $1.78 | $3.03 | **-$1.25** |

Tokens underneath: doing it itself ≈396k token-equivalents, supporting ≈618k.

### By agent

| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |
|---|---|---|---|
| claude-opus | 13 | 6.3M | $27.65 |
| local-qwen3.6-35b-a3b | 8 | 13.5M | $0.00 |

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
| f8-one-queue | 12 | 2/4 (50%) | 8 | $27.65 | -$1.25 |
| f9-line-polish | 9 | 4/10 (40%) | 25 | $2.83 | $3.35 |
| f10-crates | 0 | - | 0 | $0.00 | $0.00 |
| f11-test | 0 | - | 0 | $0.50 | $0.00 |
| f12-turn-on-notifications-little-feedback-button | 0 | - | 0 | $9.07 | $0.00 |
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
| f50-the-data-safety-review-it-asks | 0 | - | 0 | $3.17 | $0.00 |
| f51-when-a-plan-depends-on-an | 0 | - | 0 | $1.16 | $0.00 |
| f52-not-a-fan-of-the-layout | 0 | - | 0 | $0.62 | $0.00 |
| f53-why-is-milestone-diff-review-waiting | 0 | - | 0 | $1.03 | $0.00 |
| f54-the-reprioritise-up-down-arrows-do | 0 | - | 0 | $1.01 | $0.00 |
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
| f64-it-is-still-the-case-that | 0 | - | 0 | $0.45 | $0.00 |
| f64-your-review-in-planning-doesn-t | 0 | - | 0 | $0.88 | $0.00 |
| f65-the-lead-is-reviewing-stuff-but | 0 | - | 0 | $0.37 | $0.00 |
| m0 | 0 | - | 0 | $0.00 | $0.00 |
| **All** | 215 | 66/123 (54%) | 265 | $397.19 | $5.01 |
<!-- /runner report -->
