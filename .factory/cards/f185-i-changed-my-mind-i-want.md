# Milestone F185: Your answers wanted before Proposals on the desk, newest answer first

> **State:** ready · **Priority:** 4 · **Area:** factory
> Planted by the owner on 2026-10-29.

## Notes
I changed my mind I want your answers wanted section before proposals because I usually want to see answers to my questions first in the planning thread. Sign off stays first

## Today (read from the code, 2026-10-29)
`desk()` in `factory_dashboard/planning.py` returns the desk's groups in F63's order: Didn't go through, Blocked tickets, To sign off, Proposals to review, Your answers wanted, Seeds. The Overview's Needs you, the Planning tab's count, the Projects page and Previous and Next on a thread page (F35) all read `desk()`. Inside Your answers wanted, the threads the lead has answered come oldest reply first (`_last_messages` is ordered by message id), so on 2026-10-29 the top one was 42 hours old and the newest answer sat 20th.

## Outcome
On `/planning`, the desk reads: Didn't go through, Blocked tickets, To sign off, **Your answers wanted**, **Proposals to review**, Seeds. Inside Your answers wanted, the lead's newest reply comes first. Needs you, the tab count and Previous and Next follow, since they read the desk.

## Decisions
- **D1 Answers before proposals.** In `desk()`, the `answers` group moves above `proposals`. Keys, names, colours and items don't change. This reverses F63's item 3.3 and 3.4 (the owner, 2026-10-29).
- **D2 What went wrong stays above the sign-offs.** Didn't go through (F31 D9) and Blocked tickets (F106 D1) stay first. They show only when the runner refused the owner's words or blocked a ticket, and each waits on a press. "Sign off stays first" means first among the regular groups.
- **D3 Newest answer first.** Inside Your answers wanted, the threads the lead has answered come newest reply first. The dashed threads the lead still owes a reply keep F84 D4's order after them. This is F96's note for this one group; F96 stays a seed for the other groups.
- **D4 Fits F51's one-box replan.** If it is approved, f51-05 folds the proposals into the conversation's box, and the group "keeps its place in `desk()`", now right after To sign off. Nothing in f51-05 changes.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | answers-before-proposals | D | 2 | – | D1–D3 |

Not protected, and it follows F63's f63-01, so it goes to a developer. No mock-up: two groups that already exist swap places, and nothing new is drawn.

## Done when
- On `/planning`, with a ripe card, an answered thread and an open proposal, the desk shows To sign off, then Your answers wanted, then Proposals to review, then Seeds.
- Of two threads the lead has answered, the one answered last comes first.
- From the planning page, Next goes to the sign-off, then the conversation, then the proposal. Needs you on the Overview lists them in that order too.
