# Milestone F65: review rounds until you sign off

> **State:** ready · **Priority:** 9 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
What happens if I comment on a signoff/review thread? I essentially want it to iterate until I'm happy to sign off, it should show me the things it changed to see if I'm happy with the new iterated work, how clear will that be?

From the code (2026-10-09), what happens today:
- A comment on a card waiting for sign-off is a planner job like any other (`prompt` in `runner/planner.py`, `PLANNER` in `runner/prompts.py`): the lead isn't told the card is built and waiting, but it can draft follow-up tickets, and Approve plan queues them and sets the card ready (`_approve_plan` in `runner/requests.py`).
- When those tickets are done, **no new review runs**: `_reviewed` in `runner/milestone.py` sees the first review's stop in `state.review_stop`, so `due_reviews` skips the card. Its rounds are used up too (`review_counts`).
- The card ripens again at once with the **old** sheet: `_field` in `factory_dashboard/line.py` calls it ripe when every ticket is done and `milestones.signoff` is stored, and that's still the first review's. The page's "What changed" describes the first build, not the change asked for. So today it isn't clear at all.

### From F183: When I haven't signed off a ticket and approved a plan to… (merged by the lead on 2026-10-29)
When I haven't signed off a ticket and approved a plan to do some more work on top of it and the work is not done, it should not be on by desk for.me to sign off, unless I cancel the related plans that change it

What was said on F183's thread:
Asked: a card whose follow-up plan the owner approved shouldn't wait on the desk for sign-off until that work is done, unless the owner cancels the plan.
Found: once the runner has taken the approval, ready tickets already keep the card off To sign off (F172, F38, F68, F69 today). Still open: (a) between Approve and the runner's pick, the card stays in To sign off and a Sign off press is refused (F38: approved 00:24, sign-off refused 00:50 on 2026-10-29; F172 and F69 waited 07:36 to 07:50); cancelling the approval, or setting the new tickets aside, should bring the card back. (b) F142's sign-off: done in git on 10-28 (dd2f7e6, tag exists), never recorded in the database, so every press fails on `git tag … already exists` (requests 910, 921; 929 pending) and the card stays Ripe. It needs a fix ticket first in line.

### From F182: When I don't sign off a card and comment on it instead, I… (merged by the lead on 2026-10-29)
When I don't sign off a card and comment on it instead, I would like to see it orange dotted like I responded it. I wonder if that should be part of the bundling the whole task into one thing. Should sign offs be bundled with the plan and the original conversation, especially if I keep discussing the results and want to iterate on it, sounds like a step further in the bundling idea. I still want to see the tasks that are done first. Perhaps it should be styled differently if it's ripe

### From F217: if i left a comment on a sign off review, i want to see… (merged by the lead on 2026-11-04)
if i left a comment on a sign off review, i want to see that it's being revised with orange dashes in the planning desk

## Expected outcome
Commenting on a card that waits for sign-off starts a round: the lead answers and drafts the follow-up, you approve it, the line builds it, a short review checks it, and the card comes back to your desk opening on **"Round 2: what changed since your comment"**: your comment quoted, each change with how to test it, and the tickets linked. Earlier rounds fold below. Repeat until you press Sign off.

## Done when
- Pressing Approve on follow-up work for a card in To sign off takes it off To sign off at once, before the runner's pick; its page says "More work approved" where Sign off was. It is back in the rows, building, until the round is built and reviewed.
- Drop this round on its page sets the round's tickets aside, and the card comes back to To sign off with its earlier review.
- Once they're done, a review runs on the round's diff only, and writes a "This round" section answering the owner's comment.
- The card's page shows that section first, headed "Round N: what changed since your comment", with the comment quoted; the first sheet's sections stay below, under "Earlier".
- A comment on a ripe card's thread reaches the lead marked as feedback on built work, with the current sheet.
- Sign off works as it does today, at any round.
- A comment on a card in To sign off dashes its row there at once, "being revised", and the card has one row on the desk, not a second in Your answers wanted. Once the lead has replied, that row is solid again and says so.

## Before and after
- `/planning`
- `/planning/f65`

## Decisions
- **D1 A round starts at approval.** `_approve_plan` on a card whose `milestones.signoff` is stored keeps the sheet (it is the earlier round, and what comes back if the round is dropped; changed 2026-10-29 from clearing it), resets the card's `review_counts` and `review_stop`, and tags `<key>-round-<n>-start` on main before the merge. No new state or column: the card is ready, then building, as any card.
- **D2 The round's review.** `due_reviews` finds the card again once its tickets are done; `run_due_review` takes the latest round tag as its base, so the diff is the round's alone. The review prompt gets the owner's last message on the card's thread and writes a `## This round` section at the top of `.softfield/reviews/<key>.md` (what changed for the owner, how to test it, the tickets), moving the previous one under `## Earlier rounds`. The usual stop rules apply; a small diff usually stops after one round.
- **D3 The sheet gains the round.** `SIGNOFF_SECTIONS` reads `This round` as `round`; the stored sheet also keeps `round_no` and `asked` (the owner's comment). The card's page shows it first, headed "Round N: what changed since your comment", with the comment quoted, then the sheet as today under "Earlier". Picture: [`f65-mockup/round.html`](f65-mockup/round.html).
- **D4 The lead knows it's feedback.** On a card that needs sign-off, the planner prompt says so and includes the sheet's What changed. The lead answers questions on the thread, and drafts follow-up tickets only for changes. Small follow-ups follow "Who builds what" (owner, 2026-10-07).
- **D5 (dropped 2026-10-29).** Follow-ups got priority 0; the board's order is now the only order (owner, 2026-10-22), so a round runs in its card's place. Drag the card up to have it sooner.
- **D6 Drop a round.** A `set_aside` naming a card with the value `round` sets aside every ticket of the card not yet started, in one commit; the one in flight finishes. Sent before the runner took the Approve, it still works: requests run in order. The drafts stay in later/, so the owner can queue them again.
- **D7 In a round, off the desk at once.** A card is in a round from the owner's Approve press (its request still waiting) until its round's review is written: tickets ready or running, or a review job open for it. It is not ripe then. Its page keeps the review and shows "More work approved" where Sign off was, with the round's tickets and Drop this round. Picture: [`f65-mockup/round-gap.html`](f65-mockup/round-gap.html), from F38 on 2026-10-29 (approved 00:24, Sign off pressed 00:50 and refused at the 00:52 pick).
- **D8 One row for a card waiting for sign-off.** From the owner's notes on F182 and F217. While the lead owes a reply on a card in To sign off (`_waiting_for_lead`), its row there is dashed with F100's "being revised" words, its place in line and Writing now; it isn't counted. Once the lead has replied, the row is solid and counted, saying when. Either way the card's row in Your answers wanted goes. Sign off stays on its page throughout: a comment may be only a question. Its proposals stay where they are; F210, One box per card on the desk, keeps To sign off apart, and whichever is built second keeps this rule. Picture: [`f65-mockup/comment-dashes.html`](f65-mockup/comment-dashes.html).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | review-rounds | L | 7 | – | D1, D2: approval starts a round; the round's review |
| 02 | feedback-prompt | L | 3 | – | D4: the planner prompt on a ripe card |
| 03 | round-on-page | D | 4 | 01 | D3: "Round N" first on the card's page |
| 04 | drop-a-round | L | 4 | 01 | D6: Set aside a card's round |
| 05 | round-off-the-desk | D | 5 | 04 | D7: off To sign off at once; the plate and Drop this round |
| 06 | comment-dashes-sign-off | D | 3 | – | D8: one row, dashed while the lead owes a reply |

01, 02 and 04 are in `runner/` (protected): the lead's. 03, 05 and 06 are in `factory_dashboard/` and follow `_review`, `_acted_on` and `_revising`: a developer's.

F142's sign-off that fails on its existing tag is F186's (Why can't I sign off F142), answered on its own thread.
