# Milestone F63: I want to see cards in planning by order of importance.…

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
I want to see cards in planning by order of importance. Sign off first, then proposals then conversations then archives. 'comikg' can come first as it's temporary and it shows me what I've just done, like what I just planted

## Today (read from the code, 2026-10-08)
`/planning` (`factory_dashboard/templates/planning.html`) shows: the two tiles; then one row of Plant an idea, Coming (only when something is on its way) and Your desk; then Archived, closed, at the bottom. The desk's groups come from `desk()` in `factory_dashboard/planning.py`, in this order: Didn't go through, Your answers wanted (the conversations), Proposals to review, Finished, to talk through (the sign-offs), Seeds. The same order drives the Overview's Needs you, the Planning tab's count and F35's Previous and Next.

## Outcome
On `/planning`, top to bottom:
1. **Coming**, only while something is on its way (a plant, a message waiting for the lead), as wide as the page: what you just did shows first.
2. **Plant an idea**, the page's one box to write in, right under Coming, so a plant shows just above the box you typed it in.
3. **Your desk**, in this order:
   1. Didn't go through (only when the runner refused your words; usually empty);
   2. To sign off (today "Finished, to talk through");
   3. Proposals to review;
   4. Your answers wanted (the conversations);
   5. Seeds, not asked about yet.
4. **Archived**, closed, last, as today.

Needs you on the Overview and Previous and Next on the thread pages (F35) follow the same order, since they read the desk.

## Decisions
- **D1 Coming first, full width.** Coming leaves the row and sits above it, alone, shown only when it has items, as today.
- **D2 Plant stays above the desk.** It is the page's only input and what fills Coming; below the desk it would be a long scroll away on a phone. (Alternative the owner may choose: Plant after the desk, so sign-offs are the first thing after Coming.)
- **D3 Didn't go through stays first on the desk.** It holds the owner's words the runner refused (F31 D9, "never refused unseen"), shows only when there are some, and is gone once dismissed.
- **D4 The desk's order is `desk()`'s order,** so the Overview, the tab count and F35's arrows change with it: one order everywhere.
- **D5 "Finished, to talk through" becomes "To sign off":** the owner's own word, and since F50 its page has a Sign off button.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | desk-order | D | 2 | – | D1–D5 |

Not protected, follows the page's own code: a developer ticket. F14 (Coming items clickable) and F64 (the Plant box clearing) touch the same template; each stays its own card.

## Done when
- After a plant, Coming is the first thing under the tiles, above Plant an idea, on a phone and a wide screen; with nothing on its way there is no Coming.
- On the desk, a sign-off comes before a proposal, a proposal before a conversation, a conversation before a seed; Didn't go through, when there is one, is above them all.
- Needs you on the Overview lists them in the same order; Next on a thread page goes to a sign-off before a proposal.
