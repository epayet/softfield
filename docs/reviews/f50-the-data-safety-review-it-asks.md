# Review: F50, a finished card shows its review

- **Status:** done, signed off by the owner on 2026-10-08.

## Sign-off sheet

**Expected:** a card reaches "Finished, to talk through" only once its review is written. Its page then opens on what changed, how to test it and any decision waiting, and has a Sign off button.
**Done when:** with every ticket merged and no review yet, the card stays in the rows and the queue shows its review. Once the review is written, the desk says "reviewed · waits for your sign-off", and the card's page shows What changed, How to test and Decisions waiting above the conversation, with a link to the whole review. Sign off shows at once as "Signing off at the runner's next pick" (dashed orange) and the button goes.

### 1. What changed
- A card whose tickets are all merged no longer lands under "Finished, to talk through" before its review exists. It waits in the floor's rows, all its tickets done, while the review is in the queue. This is what made F20's page look empty.
- Once the review is written, the desk line reads "reviewed · waits for your sign-off".
- The card's page (`/planning/fNN`) opens with **The review**: What changed, How to test and Decisions waiting for you (only the ones it has), then a link, "The whole review", to the milestone page.
- On a card that's ready to sign off there's a **Sign off** button. Pressing it swaps the button at once for a dashed orange "Signing off at the runner's next pick". Below that, the runner's answer appears when it comes. If the runner refuses (say main has uncommitted changes), the button comes back with the runner's reason under it, even after a reload. *(The review added the at-once dashed state and the kept reason.)*

### 2. How to test it yourself
1. On your phone, open `/planning`. Under "Finished, to talk through", F20, F41 and F55 are gone (you signed them off). F50 is there and says "reviewed · waits for your sign-off".
2. Tap F50. "The review" is at the top with What changed and How to test (this sheet). "The whole review" opens the milestone page.
3. Press **Sign off**. The button goes at once and a dashed orange "Signing off at the runner's next pick" takes its place. Reload: it's still there, and the desk line for F50 is dashed too and no longer counted under Needs you.
4. After the runner's next pick, F50 leaves the desk and the floor's Ripe and moves to the stash.

### 3. Left for later
In `docs/backlog.md`, all nits:
- f50-F3: the line's replay shows a card ripe before its review was written, because nothing records when that happened.
- f50-F4: a signed-off card's page doesn't say it's signed off.
- f50-F5: the review text's numbered steps and links show as plain paragraphs and raw `[text](link)`.
- f50-F6: Archive and Remove seed still show a grey "Asked" when pressed, and only show the dashed state after a reload. Fix them the way Sign off now works.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-08, terminal session: the lead built all three tickets in one commit (`4b9fefe`), although they were planned for a developer. No runner session built them, so there's no report in `docs/sessions/`. 2026-10-08 22:51: this review's run, no tickets.
- Lessons:
  - Sign off copied Archive's button, and Archive came before your 2026-10-07 rule ("what you asked shows at once, dashed"). The proposal page's Approve button already follows the rule. When copying a button, copy the newest one.
  - D3 said the runner's answer shows under the button, but only on the same page load. A refusal disappeared on reload and the button came back with no reason. Fixed in review.
  - The report reads "0 of 3 merged" for the reason noted in F41 (backlog f41-F3): it doesn't count tickets the lead builds itself.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - F51 (the desk counts only what waits on you) is ready and reads the same desk. Fold f50-F6 (Archive's dashed state) into it, so every button on a thread page behaves the same way.
  - Hand the next developer-sized dashboard tickets to a developer. F50's three were planned for one but the lead built them, so the Known range learned nothing from them.
  - Counting tickets the lead builds itself in the report (backlog f41-F3) would stop reviews like this one reading "0 of 3".

### 7. What clogged the factory line
Nothing on this card. It was built in a terminal session and reviewed in the evening run, with no limit waits, failed attempts or stops for you.

## What was built
- **D1, ripe means reviewed** (`factory_dashboard/line.py` `_field`): a milestone with tickets but no `milestones.signoff` stays in the rows, even when all its tickets are done. `_ripe` on the desk reads the same field, so the desk and the floor agree. As a side effect, an unreviewed card whose tickets are in other states (escalated, later) now shows in the rows instead of nowhere.
- **D2, the sheet on the card's page** (`factory_dashboard/planning.py` `_review`, `Review`; `thread.html` `#review`): the three sections the owner acts on, rendered through the milestone page's escaping `_to_html`, above the conversation, plus a link to `/milestones/<key>`.
- **D3, Sign off** (`thread.html`): it posts `signoff` with the card's full key, the way Archive does, and shows "Signing off" when a request is pending.
- Tests: `test_a_card_ripens_only_once_its_review_is_written` (`test_line.py`), and four page tests in `test_planning.py` (ripe page with its sheet and button, sign-off on its way, tickets left, no review).

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f50-F1 | should-fix | claude | Pressing Sign off showed a grey "Asked: the runner will do it.", not the dashed "Signing off at the runner's next pick" the Done when and the owner's 2026-10-07 rule ask for. Only a reload showed it | Fixed: the button puts in the dashed pill at `before-request`; browser test `test_sign_off_shows_on_its_way_at_once` |
| f50-F2 | should-fix | claude | A refused sign-off (dirty main) lost its reason on reload: the button came back with its default hint, so the owner couldn't see why nothing happened (D3: "its result shows under the button") | Fixed: `Review.refused` reads the last finished sign-off while the card is still ripe; `test_a_refused_sign_off_keeps_its_word_under_the_button` |
| f50-F3 | nit | backlog | `_field`'s "reviewed" ignores the replay's moment | `docs/backlog.md` |
| f50-F4 | nit | backlog | A signed-off card's page doesn't say it's signed off | `docs/backlog.md` |
| f50-F5 | nit | backlog | `_to_html` has no numbered lists or links, and How to test is a numbered list | `docs/backlog.md` |
| f50-F6 | nit | backlog | Archive and Remove seed (older code F50 didn't touch) have the same gap as f50-F1 | `docs/backlog.md` |

Edited existing tests: the shared fixtures in `tests/factory_dashboard/conftest.py` (m4, f1 and f8 got a sign-off sheet) and `write_night`'s n0 in `test_line.py`. Both were right and needed: under D1, those milestones stay ripe only with a sheet, and none of their assertions were weakened.

No checkpoint ran (lead-built in a terminal), so there are no checkpoint findings to judge. French: nothing to check. The factory dashboard is English only and no `coucou/locale/` file changed. Gates after the fixes: `uv run pytest -q tests/unit tests/integration tests/runner tests/factory_dashboard` gives 2191 passed and 1 skipped; ruff, format and mypy are clean.

Score: 8/10. Small and correct, the sheet is escaped, and the tests cover the four page states. It missed the "at once" half of its own Done when by copying an older button.

## Workflow observations
- Third lead-built terminal milestone in a row (F41, F55, F50) with no checkpoint, where the review is the only reader. Each time it found one real gap. For lead-built work in a terminal, a Sonnet checkpoint on the commit before the review would cost about $0.25 and would likely have caught f50-F1, since the Done when spells it out.
- Developer tickets the lead builds itself leave the Known range unchanged: F50 tells us nothing about a developer on difficulty 2–3 dashboard tickets.

<!-- runner report -->
## Numbers

_Written by `uv run runner report f50-the-data-safety-review-it-asks` from the metrics database, which isn't in git: a snapshot. Run it again to refresh; edit outside these markers._

| Result | F50-THE-DATA-SAFETY-REVIEW-IT-ASKS |
|---|---|
| Tickets merged | 0 of 3 |
| First-attempt pass rate | - |
| Local attempts | 0 |
| Escalations, directions, checkpoints | 0, 0, 0 |
| Review rounds | 1 |
| Findings | none |
| Local model | 0 tokens (0 in, 0 out) |
| Claude | $2.06 (477k token-equivalents) |

### Savings from delegating

What Claude would have spent writing the lines the developers merged, against what it spent supporting them: tickets, directions, escalations, and a share of the reviews and checkpoints (f1 D7). API-equivalent dollars.

| Developer | Tickets | Lines | Doing it itself | Supporting | Net |
|---|---|---|---|---|---|
| **All** | 0 | 0 | $0.00 | $0.00 | **$0.00** |

Tokens underneath: doing it itself ≈0 token-equivalents, supporting ≈0.

### By agent

| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |
|---|---|---|---|
| claude-opus | 2 | 477k | $2.06 |

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
| f9-line-polish | 9 | 4/10 (40%) | 25 | $2.83 | $3.35 |
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
| f50-the-data-safety-review-it-asks | 0 | - | 0 | $2.06 | $0.00 |
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
| f63-there-are-items-finished-to-talk | 0 | - | 0 | $0.44 | $0.00 |
| f64-it-is-still-the-case-that | 0 | - | 0 | $0.45 | $0.00 |
| f65-the-lead-is-reviewing-stuff-but | 0 | - | 0 | $0.37 | $0.00 |
| m0 | 0 | - | 0 | $0.00 | $0.00 |
| **All** | 214 | 66/122 (54%) | 262 | $387.31 | $7.45 |
<!-- /runner report -->
