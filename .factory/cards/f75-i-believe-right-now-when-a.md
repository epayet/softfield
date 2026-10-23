# Milestone F75: I believe right now, when a plan gets approved or…

> **State:** ready · **Priority:** 8 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
I believe right now, when a plan gets approved or rejected, it archives the conversation thread that goes with it. currently if i approve or reject a proposal and that it's on its way, the proposal is displaying 'on its way' with the orangely dotted line which is great. assuming this action will archive the thread as well, currently it doesn't look like the thread will be archived. i want it to be displayed as much as well, so that i know that this thread will soon be archived too

## Why it happens (read from the code, 2026-10-09)
- The owner is right: since f31-01, `_close_if_settled` in `runner/requests.py` archives a thread once every proposal of its latest set is settled (approved, rejected, or a merge whose card has left main), with a lead line ("Approved by the owner on …").
- It runs only when the runner applies the approval or the reject, at its next pick. Until then `_open_proposals` dashes the proposal (`proposal_state` says `on its way`), but the thread's own box in "Your answers wanted" stays solid and counted: `_acted_on` in `factory_dashboard/planning.py` dashes a thread only for a manual `archive`, `signoff` or `drop_seed`.

## Outcome
- **The thread shows it's leaving, at once:** when your Approve or Reject settles the last open proposal of the lead's latest reply, the thread's box in "Your answers wanted" turns dashed orange at the same moment as the proposal, says "archiving at the runner's next pick", and no longer counts as waiting for you.
- **Its page says the same:** the thread shows the "Archiving at the runner's next pick" mark a manual Archive shows today.
- **Only when it will really go:** approving one proposal while another of the same reply is still open leaves the thread solid, because the runner won't archive it.

## Decisions
- **D1 Same rule as the runner.** A thread is archiving when every proposal of its latest set is approved, rejected, a merge one of whose cards has left main (`_gone_merge`), or on its way (`proposal_state` over the owner's requests since that message), and at least one is on its way. This is `_close_if_settled`'s rule with "on its way" counted as settled.
- **D2 A pending reject takes every draft.** A reject on an `adr`, `mockup`, `plan` or `replan` drops the plan branch (F31 D2), so while it's pending every draft-carrying proposal of that set counts as on its way too; otherwise rejecting the plan of a reply that also drafted an ADR would leave the box solid until the pick.
- **D3 One words, one look.** The same words and dashed edge a manual Archive uses ("archiving at the runner's next pick"); no new wording for approve against reject. Once the runner archives it, it shows under Archived with its reason (`approved` or `rejected`), as today.
- **D4 A refusal brings it back.** If the runner refuses the approval, the proposal is open again (`proposal_state`), so the thread goes solid and counted again on the next refresh. Nothing extra to build.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | archiving-on-approval | D | 3 | f74-01, f22-01 | D1–D4 on the desk and the thread page |

Follows `_acted_on` and `_open_proposals` in the same file: a developer ticket. After f74-01, which rewrites `_answers_wanted` and the dashed thread boxes, and f22-01, which moves the thread page's archive mark to the bottom.

## Done when
- Approve the plan of a thread whose reply proposed only that plan: on `/planning` the proposal and the thread's box are both dashed orange at once, the thread's box says "archiving at the runner's next pick", and the Planning tab's count drops by it.
- Open the thread: it shows "Archiving at the runner's next pick".
- Approve one of two open proposals of the same reply: the thread's box stays solid.
- After the runner's pick: the thread is under Archived as approved (or rejected).
