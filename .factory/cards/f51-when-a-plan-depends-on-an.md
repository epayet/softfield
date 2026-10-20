# Milestone F51: when a plan depends on an adr i have approved but is waiting for planner

> **State:** ready · **Priority:** 7 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
i can't do anything about it, so it shouldn't count as something on my desk for me to urgently look at (blocked)

### From F16: Planning still says your answer wanted even though I answered (merged by the owner on 2026-10-08)
If I answered but it's not picked yet, it should not behave as if it does. It should count, at least visually in the front-end that I've done what I needed

##### From F24: bug: when i answer a ticket in planning it is in both the "your desk" and "coming" sections (merged by the owner on 2026-10-07)
side qouestion: how to call those things on the desk keeping the factory theme, i called it ticket but that's not quite that yet. seed?

### From F105: In a group proposal where there is a bundle of an adr and… (merged by the lead on 2026-10-10)
In a group proposal where there is a bundle of an adr and a plan. I currently can't approve the plan until I've approved the adr. Which is fine, but if the adr approval is on its way to it's runner pick next, I want the ability to approve the plan as well if we know the plan is on its way to being approved

### From F157: if i archive something that got merged, it does'nt archive… (merged by the lead on 2026-10-20)
if i archive something that got merged, it does'nt archive the merged plan right? i just archived f156, so just checking. there are tickets i believe about being smarter when doing actions (approve adr means approve plan for example)

What was said on F157's thread:
The owner asked whether archiving F156 (merged into F135) also archived F135. Answer: no, Archive touches only its own thread. F135 was archived separately by the owner four minutes later, and its ticket f135-01 still runs. They also asked about the tickets for 'smarter actions' (Approve ADR then Approve plan at once), which are F51's f51-01 and f51-02. Nothing is still open.

## Outcome
The desk, the Planning tab's count and the Overview's "Needs you" count only what the owner can do now (the owner, 2026-10-08):
- A card with an ADR and a plan: before the ADR is accepted, the desk shows **one** item, the ADR, "then its plan". The plan isn't a second thing to do.
- Once the owner presses Accept ADR, they can press Approve plan straight away, without waiting for the runner's next pick: the runner accepts the ADR first, then approves the plan, in the order they were asked.
- A thread the owner has answered leaves "Your answers wanted" at once, and shows only in Coming until the lead replies (F16's bug, from F24).

## What was wrong (from the code, 2026-10-08)
- `_open_proposals` in `factory_dashboard/planning.py` lists every open proposal, so a card's plan counts on the desk beside its ADR, though Approve plan stays disabled until the ADR is Accepted on main (`_adr_waits`).
- An Accept ADR request is applied only at the runner's next pick, which can be most of an hour away. Until then the plan sits under "Proposals to review", counted, with a greyed Approve plan: on the desk, but nothing to do.
- `_answers_wanted` ignores an open `plan_message` request, so an answered thread is in both "Your answers wanted" and Coming.

## Decisions
- **D1 One item per card's ADR and plan:** while a card's `adr` proposal is open (not accepted on main, no Accept ADR on its way), its `plan` and `replan` proposals aren't desk items of their own; the ADR's item adds "· then its plan". Send back on the plan still works from the thread.
- **D2 Approve plan once Accept ADR is asked:** `_adr_waits` counts an open `accept_adr` request for that ADR as accepted, so the plan's item is back on the desk and Approve plan is enabled, with the line "ADR N's acceptance is on its way: the runner applies it first." Requests are applied oldest first (`metrics.open_requests`), so the accept lands before the approval.
- **D3 The runner's guard:** `_approve_plan` refuses ("relies on ADR N, still Proposed: accept it first") when the merged branch leaves an ADR Proposed that the branch drafted. So a failed accept can't let its plan through. Today a branch's new Proposed ADR passes `_owners_marks`.
- **D4 Answered is answered (F16):** a thread with an open `plan_message` request isn't in "Your answers wanted"; Coming already shows it.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | desk-counts-what-waits-on-you | D | 3 | – | D1, D4 |
| 02 | approve-plan-after-accept | L | 4 | – | D2, D3 (runner is protected) |

## Done when
- Plant a card whose plan has an ADR: the desk shows one item, the ADR, "then its plan", and the count is 1.
- Press Accept ADR: on the plan's page, Approve plan is enabled at once; press it. At the runner's next pick the ADR is accepted, then the plan approved and its tickets queued.
- Reply on a thread: it leaves "Your answers wanted" at once and shows in Coming only.
