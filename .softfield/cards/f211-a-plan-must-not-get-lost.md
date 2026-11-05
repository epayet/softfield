# Milestone F211: Open plans survive a card's closing, and new ideas don't join a planned card

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-03.

## Notes
A plan must not get lost when its card closes. Don't merge a new idea into a card whose plan is already approved unless that plan covers it; give it its own card. Sign-off and Archive must say when a plan is still open on the card, and let me keep it as a new card.

### From F223: I've signed off f149 but I don't remember if I asked it to… (merged by the lead on 2026-11-05)
I've signed off f149 but I don't remember if I asked it to do some more work. Clarify what happens in this situation

What was said on F223's thread:
Asked: the owner signed off F149, Retire the backlog file, did not remember whether they had asked it for more work, and wants to know what happens in that situation.
Answered for F149: they asked on 2026-11-04. ADR 43 was accepted and its plan approved that day, and the sign-off was on 2026-11-05 with no message waiting. The work is f164-07-review-fixes-are-quoted-too, ready on F164, not started, and waiting for f164-01 and f164-03.
Still to answer, from the code: `owner.signoff` refuses only when the card's own tickets are ready or stopped. Tickets on another card carry on untouched. A message still waiting doesn't stop a sign-off, and the lead still answers on the thread while the card stays done. An open plan doesn't stop one either. Approving a plan after sign-off sets the card back to ready, its tickets run, and `due_reviews` skips a signed-off card, so that work gets no review.
Still open, the gap for F211's plan: an approved plan whose ticket sits on another card fires neither F211 warning. The only trace is the 'queued f164-07' line on the thread. Suggested fix: one line by Sign off and on the done card's page naming that ticket, its card and whether it has run, added to f211-03 and its mock-up.
