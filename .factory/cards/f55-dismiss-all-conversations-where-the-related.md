# Milestone F55: Clear out the threads already settled

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-08. Base: git tag `f55-dismiss-all-conversations-where-the-related-start`. Report: [`.factory/reviews/f55-dismiss-all-conversations-where-the-related.md`](../reviews/f55-dismiss-all-conversations-where-the-related.md).
> Planted by the owner on 2026-10-08 as "dismiss all conversations where the related plans have been accepted".

## Notes
dismiss all conversations where the related plans have been accepted

### From F56: dismiss all conversations where the work has already been doned or planned (merged by the owner on 2026-10-08)
(none)

## Outcome
- **The desk starts clean:** every thread whose plan the owner already approved, or whose card was merged away, leaves "Your answers wanted" and Needs you once, and shows under Archived as approved.
- **A merged card's thread doesn't come back:** a merge archives the duplicate's thread along with its line pointing to the kept card.
- **Nothing live is hidden:** a thread with a proposal still open, or one the owner opened again, stays.

## Decisions
- **D1 Going forward is F31's:** F31 D1 (ticket f31-01, ready) archives a thread once every proposal of its latest set is settled. F45 ("When I approve a plan it should close the related conversation") was merged into F31 for that. F55 adds only what F31 leaves out: the threads settled before f31-01 lands, and merged cards' threads.
- **D2 Why they stay today:** approving a plan writes no message, so the lead's reply stays the thread's last and `_answers_wanted` in `factory_dashboard/planning.py` lists it until the owner archives it by hand. `_merged` in `runner/requests.py` adds a lead line to the duplicate's thread, so a merged card (F45, F47) also lands in "Your answers wanted", titled by its bare key.
- **D3 The clear-out, once:** at the first runner start after it lands, a one-off step archives each open thread (not the general one) whose card is ready, building, needs sign-off or done, or no longer has a card, and whose latest set has no proposal open by F31 D3's state. Reason `approved`, its `planning` item resolved, as `_archive` does. It runs once, so a thread the owner opens again later is never touched by it.
- **D4 Merges archive:** from then on `_merged` archives the duplicate's thread (reason `approved`) after its line.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | archive-settled-threads | L | 4 | f31-01 | D3, D4 |

## Done when
- Open `/planning` after it lands: no card whose plan you approved is under "Your answers wanted", and F45 and F47 aren't either; they are under Archived as approved.
- A card with a proposal still waiting for you stays on the desk.

## Not here
- Archiving at approval from now on: F31 D1.
