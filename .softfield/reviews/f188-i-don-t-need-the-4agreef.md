# Review: F188, the count leaves the review's phone bar

## Sign-off sheet

### 1. What changed
On a phone, the bar stuck to the bottom of a review page (a plan, a mock-up, an ADR) no longer shows "4 agreed · 0 to change". It holds just the button (Approve plan, Accept ADR, or "Send 1 change back" once you comment) at the left and the closed Reject… fold at the right edge. The yellow dots above the points still show which ones you commented on. On a wide screen nothing changes: the count still shows in the side panel and still updates as you write.

Mock-up: [`f188-mockup/review-dock.html`](../cards/f188-mockup/review-dock.html). No after pictures for this card, so nothing to compare.

### 2. How to test it yourself
1. On your phone, open a card in the planning room that has a plan or ADR waiting, and open its review page.
2. The bottom bar shows the button on the left and "Reject…" on the right, with no "agreed · to change" text, on one row.
3. Tap "Comment…" on a point and write a word: the button reads "Send 1 change back", still with no count.
4. Tap "Reject…": it opens on a row of its own.
5. On the computer, open the same page: the count shows above the button and changes as you comment.

### 3. Left for later
Nothing from this card. Two test-quality notes from F179's checkpoint (the weak 390 px overflow test, a stray running `triage` job in the shared fixture) belong to F179's review, not this one.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-05 ([session](../sessions/2026-11-05-1656.md)): one ticket, merged by the local model on its first attempt in 35 min (3.4M local tokens in), no gate failure. The lead's review fixed three small points directly.
- Lessons:
  - The developer edited the template the ticket said to leave alone, to add an empty spacer. A `margin-left: auto` does it in CSS; I fixed it rather than send it back (a few lines).
  - Its second test copied a heavy git setup from a mock-up test it didn't need. The ticket's "the count still updates on a wide screen" had no test; now it has.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** when a ticket says "leave file X as it is", the runner already flags "changed files outside `files:`"; that flag could go to the checkpoint as a question ("why?") for a difficulty-1 UI ticket, which would have caught F1 before the review.

### 7. What clogged the factory line
- **The wait in the queue:** planned 2026-10-29 08:20, built 2026-11-05 19:12, about 7.5 days, all of it waiting its turn on the board behind other cards. Not a loss: that is the board's order working. Unclog: nothing to change.
- **The build itself:** 35 min of one local attempt, no failures, no waits for limits, no stops for you.

## What was built
- `factory_dashboard/static/dashboard.css`: in the phone rules, `#review-count` is hidden and the closed Reject… fold is pushed to the right edge.
- `tests/factory_dashboard/test_thread.py`: `test_the_dock_is_compact_on_a_phone` now checks the count is hidden at 390 px, the button and the fold share the bar's one row with the fold in its right half, and the count shows on a wide screen; `test_a_comment_writes_send_one_change_back_with_no_count` checks "Send 1 change back" with no count on a phone, and that the wide-screen count reads "· 1 to change".

## Findings and resolutions
| Id | Grade | What | Route |
|---|---|---|---|
| F1 | should-fix | An empty `.dock-gap` span added to `proposal.html` (the ticket said leave the template alone) added an extra 8 px gap on wide screens | fixed by the lead: span gone, `margin-left: auto` on the closed fold |
| F2 | should-fix | The new comment test built a plan branch it didn't need, writing `ADR_ON_MAIN` with a literal `{status}`; the wide-screen count update wasn't tested | fixed by the lead; the new fold-position check was confirmed to fail without the CSS rule |
| F3 | nit | Three CSS lines indented 3 spaces; the f42 comment still listed the count in the row | fixed by the lead |

Edited existing tests: `test_the_dock_is_compact_on_a_phone` was rewritten to the ticket's new rule; no check was weakened beyond dropping the count from the row (the change the card asked for).

No checkpoint ran on this card's work, so there are no checkpoint verdicts. Score: 7 (right result on the first try, but a template edit against the ticket and a sloppy second test).

French: none; the dashboard is English only.

## Factory
- One local developer job, passed first time; one planner job on Opus ($0.87); this review on Opus. No escalations, no parks, no stops for the owner.
- The runner's "changed files outside `files:`" note was the right signal for F1; see What next.

<!-- runner report -->
<!-- /runner report -->
