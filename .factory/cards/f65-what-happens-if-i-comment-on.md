# Milestone F65: review rounds until you sign off

> **State:** ready · **Priority:** 5 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
What happens if I comment on a signoff/review thread? I essentially want it to iterate until I'm happy to sign off, it should show me the things it changed to see if I'm happy with the new iterated work, how clear will that be?

From the code (2026-10-09), what happens today:
- A comment on a card waiting for sign-off is a planner job like any other (`prompt` in `runner/planner.py`, `PLANNER` in `runner/prompts.py`): the lead isn't told the card is built and waiting, but it can draft follow-up tickets, and Approve plan queues them and sets the card ready (`_approve_plan` in `runner/requests.py`).
- When those tickets are done, **no new review runs**: `_reviewed` in `runner/milestone.py` sees the first review's stop in `state.review_stop`, so `due_reviews` skips the card. Its rounds are used up too (`review_counts`).
- The card ripens again at once with the **old** sheet: `_field` in `factory_dashboard/line.py` calls it ripe when every ticket is done and `milestones.signoff` is stored, and that's still the first review's. The page's "What changed" describes the first build, not the change asked for. So today it isn't clear at all.

## Expected outcome
Commenting on a card that waits for sign-off starts a round: the lead answers and drafts the follow-up, you approve it, the line builds it, a short review checks it, and the card comes back to your desk opening on **"Round 2: what changed since your comment"**: your comment quoted, each change with how to test it, and the tickets linked. Earlier rounds fold below. Repeat until you press Sign off.

## Done when
- Approving follow-up tickets on a card that has a sheet takes it off the desk and the floor's Ripe: it is back in the rows, building.
- Once they're done, a review runs on the round's diff only, and writes a "This round" section answering the owner's comment.
- The card's page shows that section first, headed "Round N: what changed since your comment", with the comment quoted; the first sheet's sections stay below, under "Earlier".
- A comment on a ripe card's thread reaches the lead marked as feedback on built work, with the current sheet.
- Sign off works as it does today, at any round.

## Decisions
- **D1 A round starts at approval.** `_approve_plan` on a card whose `milestones.signoff` is stored clears it (the report file keeps every round), resets the card's `review_counts` and `review_stop`, and tags `<key>-round-<n>-start` on main before the merge. No new state or column: the card is ready, then building, as any card.
- **D2 The round's review.** `due_reviews` finds the card again once its tickets are done; `run_due_review` takes the latest round tag as its base, so the diff is the round's alone. The review prompt gets the owner's last message on the card's thread and writes a `## This round` section at the top of `.factory/reviews/<key>.md` (what changed for the owner, how to test it, the tickets), moving the previous one under `## Earlier rounds`. The usual stop rules apply; a small diff usually stops after one round.
- **D3 The sheet gains the round.** `SIGNOFF_SECTIONS` reads `This round` as `round`; the stored sheet also keeps `round_no` and `asked` (the owner's comment). The card's page shows it first, headed "Round N: what changed since your comment", with the comment quoted, then the sheet as today under "Earlier". Picture: [`f65-mockup/round.html`](f65-mockup/round.html).
- **D4 The lead knows it's feedback.** On a card that needs sign-off, the planner prompt says so and includes the sheet's What changed. The lead answers questions on the thread, and drafts follow-up tickets only for changes. Small follow-ups follow "Who builds what" (owner, 2026-10-07).
- **D5 Follow-ups go first.** A ripe card's follow-up tickets get priority 0, so the owner isn't kept waiting behind the backlog.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | review-rounds | L | 7 | – | D1, D2, D5: approval starts a round; the round's review |
| 02 | feedback-prompt | L | 3 | – | D4: the planner prompt on a ripe card |
| 03 | round-on-page | D | 4 | 01 | D3: "Round N" first on the card's page |

01 and 02 are in `runner/` (protected): the lead's. 03 is in `factory_dashboard/` and follows `_review`'s sections: a developer's.
