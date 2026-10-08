# Review: F41, the points carry everything

## Sign-off sheet

**Expected:** on a thread, you read the lead's points and nothing else; the lead says everything once, in the points, and its free text is folded shut, there only if you want it.
**Done when:** a reply with points shows its text in a closed "Full reply" above them; a reply without points (its block broken) shows its text open; the planner writes at most two short lines before its block and never a "no duplicate" point.

### 1. What changed
- On a planning thread, each lead reply now shows its points first. Its free text sits in a closed **Full reply** fold above them; tap it to read the text as before.
- A reply whose points couldn't be read still shows its text open, with the note saying why.
- From the next reply on, the lead writes at most two short lines before its points, and no point says "I checked and found nothing" (F44's ask, merged into this card).
- Found in review and fixed: when the runner can't apply a merge the lead proposed (F49), its "didn't apply it, waits for your Approve" now shows as a point of its own, not hidden in the folded text.

### 2. How to test it yourself
1. On your phone or desktop, open `/planning`, then a thread whose last lead reply has points (any recent card).
2. The points come first under a one-line **Full reply**; tap it and the text reads as before.
3. Send a short message on any card (e.g. "anything to add?"). When the reply arrives: at most two lines of text in the fold, everything else in the points, and no point saying "no duplicate" or "no conflict".
4. If a reply ever shows text open with no points, its last line says why its points weren't read.

### 3. Left for later
- Backlog: `runner report` counts only the runner's merges, so this card's two tickets, built in a terminal session, read "0 of 2 merged" below (f41-F3).
- Not in this card, as planned: F30 (newest answer first) and F42 (the proposal card's small scroll area).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-08, terminal session with the owner: f41-01 and f41-02 built by the lead and committed together (`fcb2d0c`); no runner session, so no report in `docs/sessions/`. 2026-10-08 17:50 ([session](../sessions/2026-10-08-1750.md)): this review's run, no tickets.
- Lessons:
  - Folding a field hides everything else that writes to it. F49's merge note was appended to the same text the same day; reading every writer of `reply.text` found it. Fixed in review.
  - A test comment claimed a case the fixture didn't have (the owner's message). Read a test's claims against its data.
  - Lead-built terminal work escapes the runner's numbers; the backlog item fixes the count.

### 6. What next
- **Product:** on hold, as you asked. When it resumes, the same idea fits Mum's side: show what she needs (a photo, a word) and fold the rest.
- **Factory:**
  - F30 (newest answer first) is the natural next card on the same page; with the text folded, a thread is now short enough that latest-first reads well.
  - Count terminal-built tickets in the report (backlog f41-F3), so a milestone built with you doesn't read as zero.
  - Watch the next few replies: if the lead still writes long text before its block, add a check that trims it to two lines and keeps the rest (no refusal: your rule on never losing words).

### 7. What clogged the factory line
Nothing on this card: both tickets were built and committed in one terminal session, and the review ran right after the F20 verdict. No limit waits, failed attempts or stops.

## What was built
- **f41-01** (`runner/prompts.py`): the planner's "How to answer" says the points in the `json` block carry every answer, risk, question and ask; the text before the block is at most two short lines, or nothing; no point reports a check that found nothing, while a repeat found is still a point and a `merge`. Test: `test_the_prompt_puts_everything_in_the_points_and_no_empty_checks` (card and general thread).
- **f41-02** (`factory_dashboard/templates/thread.html`): a lead message with points and text renders its text in a closed `<details class="full-reply">` before the points (44px summary, styled like "Remove seed"); without points, the text shows open; owner messages unchanged. Test: `test_a_reply_with_points_folds_its_text_and_one_without_shows_it`.
- The history the next planner job reads (`planner.history`) and the repo export (`planner.export`) still carry the full text (D4).

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f41-F1 | should-fix | claude | F49's `_auto_merge` appended "the runner didn't apply this merge" to the lead's text, now folded shut; the owner would see an open merge with no reason (`runner/loop.py`) | Fixed: with points, each refusal is a point (title, reason, "It waits for your Approve."); without, it stays in the open text. The F49 test now checks the point. |
| f41-F2 | nit | claude | A reply with points and no text (now allowed by D1) rendered an empty paragraph; the fold test claimed to cover the owner's message but had none | Fixed: `elif msg.text`; the test adds an owner message and a textless reply. |
| f41-F3 | nit | backlog | The report reads "0 of 2 merged" for terminal-built tickets | `docs/backlog.md` |

No checkpoint ran on this card (lead-built in a terminal), so there are no checkpoint findings to judge. French: nothing to check; the factory dashboard is English only and no `coucou/locale/` file changed. Gates after the fixes: `pytest` (2145 passed, 1 skipped), `ruff`, `mypy` green.

Score: 8/10. Small, clear, and the prompt and fold do what the card asks; one interaction with the same day's F49 slipped through.

## Workflow observations
- f41-02 was a developer ticket by the owner's "who builds what" rule; building it with f41-01 in the owner's session was quicker than queueing a 10-line template change, and fine for that reason.
- No checkpoint sees lead-built terminal work, so the review is its only reader; with two milestones (F41, F49) touching the planner reply on the same day, that's where the gap hid.

<!-- runner report -->
## Numbers

_Written by `uv run runner report f41-i-find-that-on-conversations-there` from the metrics database, which isn't in git: a snapshot. Run it again to refresh; edit outside these markers._

| Result | F41-I-FIND-THAT-ON-CONVERSATIONS-THERE |
|---|---|
| Tickets merged | 0 of 2 |
| First-attempt pass rate | - |
| Local attempts | 0 |
| Escalations, directions, checkpoints | 0, 0, 0 |
| Review rounds | 1 |
| Findings | none |
| Local model | 0 tokens (0 in, 0 out) |
| Claude | $1.13 (225k token-equivalents) |

### Savings from delegating

What Claude would have spent writing the lines the developers merged, against what it spent supporting them: tickets, directions, escalations, and a share of the reviews and checkpoints (f1 D7). API-equivalent dollars.

| Developer | Tickets | Lines | Doing it itself | Supporting | Net |
|---|---|---|---|---|---|
| **All** | 0 | 0 | $0.00 | $0.00 | **$0.00** |

Tokens underneath: doing it itself ≈0 token-equivalents, supporting ≈0.

### By agent

| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |
|---|---|---|---|
| claude-opus | 2 | 225k | $1.13 |

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
| f41-i-find-that-on-conversations-there | 0 | - | 0 | $1.13 | $0.00 |
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
| f55-dismiss-all-conversations-where-the-related | 0 | - | 0 | $1.06 | $0.00 |
| f56-dismiss-all-conversations-where-the-work | 0 | - | 0 | $0.58 | $0.00 |
| f57-reprioritise-for-me-while-i-dont | 0 | - | 0 | $0.92 | $0.00 |
| f58-when-i-ask-the-lead-a | 0 | - | 0 | $0.60 | $0.00 |
| f59-periodic-review-of-the-factory | 0 | - | 0 | $0.00 | $0.00 |
| f60-suggest-improvements-to-ai-workflow | 0 | - | 0 | $0.00 | $0.00 |
| f61-on-claude-usage-page-there-is | 0 | - | 0 | $0.00 | $0.00 |
| f62-claude-opus-review-on-overview-does | 0 | - | 0 | $0.00 | $0.00 |
| m0 | 0 | - | 0 | $0.00 | $0.00 |
| **All** | 214 | 66/121 (55%) | 258 | $383.05 | $8.10 |
<!-- /runner report -->
