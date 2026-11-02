# Milestone F73: I want to be able to mark a proposal as parked for now

> **State:** done · **Priority:** 8 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-02. Base: git tag `f73-i-want-to-be-able-to-start`. Report: [`.factory/reviews/f73-i-want-to-be-able-to.md`](../reviews/f73-i-want-to-be-able-to.md).
> Planted by the owner on 2026-10-09.

## Notes
I want to be able to mark a proposal as parked for now

### From F107: In a recent conversation about blocked tickets, We've… (merged by the lead on 2026-10-13)
In a recent conversation about blocked tickets, We've decided to have a 'set aside' button for things that we started but want to park for now. I'd like to have that for all proposals in fact. That makes me think that how will I see those in the planning desk then, will I need a new 'later' section to bring bacon proposals/milestones that were previously discussed/worked on? How related to 'arcjived' is this.

## Expected outcome
- Every proposal's review page has "Set aside": the conversation leaves the desk, its drafts stay, and a message from the owner opens it again.
- The planning desk lists what was set aside under "Set aside · N", apart from "Archived", which keeps what is finished. Set-aside things are never counted as waiting for the owner.
- A proposal that has waited says how old its draft is before the owner approves it.

## Done when
- On a phone, open a proposal, press "Set aside": it shows on its way at once, and after the runner's next pick the conversation is under "Set aside" on the desk, saying what waits in it ("1 plan, 1 mock-up · set aside 2 minutes ago"), and no longer under "Proposals to review".
- A thread closed by an approval or a rejection is under "Archived", not "Set aside".
- Open a proposal set aside three days ago or more: beside Approve it reads "Drafted N days ago … ask the lead to refresh it".

## Decisions
Agreed with the owner on F107's thread (2026-10-13), planned in the terminal session of the same day.
- **D1 "Set aside" is Archive, said plainly.** No new state, no new request and nothing in the runner: the button posts the `archive` request the thread page's Archive button posts. What tells the two lists apart is read, not stored: a thread the owner archived (`archived_why` is `by you`) whose latest proposals still hold an open one is set aside; every other archived thread is finished.
- **D2 The whole conversation, not one proposal.** A reply's drafts live together on the card's plan branch, so they are set aside together.
- **D3 "Set aside", not "Later".** The Tickets page already has a Set aside table, and F106's button for a blocked ticket uses the same words. The list sits just above Archived, closed, and counts in no "needs you".
- **D4 A stale draft says so.** From three days on, beside Approve: "Drafted N days ago: the code may have moved. Ask the lead to refresh it before approving." Approve stays; the runner's own pre-flight still refuses a plan that no longer applies.
- **D6 "Refresh against main", one press** (the owner, 2026-10-13: "would a 'update/recheck plan with latest' be useful?"). A button on an open plan, mock-up or replan that sends it back with a fixed request to recheck it against main. No new request and nothing in the runner: it is Send back with the words written. Called Refresh, not Replan: a replan already means changing a card's queued tickets.
- **D5 Cards already in the queue are left out.** Setting aside a card whose tickets are queued means taking them out and bringing them back in order, which is runner code. The board's order (F15) and F106's button for one blocked ticket cover it for now.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | set-aside-list | D | 4 | f22-01, f26-02 | D1, D3: the "Set aside" list on the desk, apart from Archived |
| 02 | set-aside-button | D | 4 | 01, f42-01 | D2, D4, D6: Set aside and Refresh on a proposal's page, and the stale note |
