# Milestone F51: when a plan depends on an adr i have approved but is waiting for planner

> **State:** ready · **Priority:** 2 · **Area:** factory
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

### From F99: When a proposal has bundled things like both a mock-up and… (merged by the lead on 2026-10-20)
When a proposal has bundled things like both a mock-up and and a plan. Bundle them in tbr planning list too. Right now it looks like I have 2 things to look into but one approval approves both. Like the current both f54

### From F176: Conversations and proposals can be better bundled… (merged by the lead on 2026-10-27)
Conversations and proposals can be better bundled together. I find myself opening the conversations first and if I'm happy with the latest discussion I look at the adr and proposals. In planning page I have to jump between them. I believe there is a conversation and plan about building proposals better, I wonder if we can go a step beyond and bundle the conversation with it tol (unless that was already the plan)

## Outcome
The desk, the Planning tab's count and the Overview's "Needs you" count only what the owner can do now (the owner, 2026-10-08):
- A card's proposals (an ADR, a plan, mock-ups, merges) are **one** desk item, since one or two presses settle them all (F99). Before the ADR is accepted, the item says so; the plan isn't a second thing to do.
- Once the owner presses Accept ADR, they can press Approve plan straight away, without waiting for the runner's next pick: the runner accepts the ADR first, then approves the plan, in the order they were asked.
- A thread the owner has answered leaves "Your answers wanted" at once, and shows only in Coming until the lead replies (F16's bug, from F24).

## What was wrong (from the code, 2026-10-08)
- `_open_proposals` in `factory_dashboard/planning.py` lists every open proposal, so a card's plan counts on the desk beside its ADR, though Approve plan stays disabled until the ADR is Accepted on main (`_adr_waits`).
- An Accept ADR request is applied only at the runner's next pick, which can be most of an hour away. Until then the plan sits under "Proposals to review", counted, with a greyed Approve plan: on the desk, but nothing to do.
- `_answers_wanted` ignores an open `plan_message` request, so an answered thread is in both "Your answers wanted" and Coming.

## Seen on the desk (2026-10-20)
- "Proposals to review" has ten items for five cards: F27's ADR 27, plan and merge of F34; F154's, F158's and F159's plan and mock-up each; F153's plan. One press settles each card's plan, mock-up and merge (`_about` in `runner/planner.py`), so the desk counts five things that aren't there.
- An item the owner has acted on now shows dashed and leaves the count (`waiting_for_you`), but F27's plan and merge still count while its ADR waits.

## Decisions
- **D1 One item per card (revised 2026-10-20, with F99):** a card's open proposals are one desk item, not one each: its ADR, plan, replan, mock-ups and merges, since one Accept ADR and one Approve plan settle them all. The picture is `.factory/cards/f51-mockup/desk-bundles.html`.
  - Its title is the plan's (else the first proposal's), with the card's key; its parts are listed in the order they are settled (ADR first), each still to do or on its way; its words are the key points' total, plus "accept the ADR first" while the ADR is open.
  - It links to the first part still to do. It counts until every part is on its way, then shows dashed like any request on its way.
  - The general thread's seeds and merges stay one item each: each is settled by its own press.
  - Send back on any part still works from its page.
- **D2 Approve plan once Accept ADR is asked:** `_adr_waits` counts an open `accept_adr` request for that ADR as accepted, so the plan's item is back on the desk and Approve plan is enabled, with the line "ADR N's acceptance is on its way: the runner applies it first." Requests are applied oldest first (`metrics.open_requests`), so the accept lands before the approval.
- **D3 The runner's guard:** `_approve_plan` refuses ("relies on ADR N, still Proposed: accept it first") when the merged branch leaves an ADR Proposed that the branch drafted. So a failed accept can't let its plan through. Today a branch's new Proposed ADR passes `_owners_marks`.
- **D5 An empty list keeps the last one (2026-10-20):** a lead reply listing no proposals is stored as `'[]'`; the thread and the review pages skip it as the desk does, so the earlier proposals keep their buttons.
- **D4 Answered is answered (F16):** a thread with an open `plan_message` request isn't in "Your answers wanted"; Coming already shows it.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | desk-counts-what-waits-on-you | L | 4 | – | D1 (revised), D4 |
| 03 | empty-list-keeps-proposals | D | 2 | – | a lead reply with no proposals hid F51's replan on 2026-10-20 (D5) |
| 02 | approve-plan-after-accept | L | 4 | – | D2, D3 (runner is protected) |

## Done when
- A card with an ADR, a plan and a merge: the desk shows one item, its parts in order, "accept the ADR first", and the count is 1. A card with a plan and a mock-up: one item too.
- Press Accept ADR: on the plan's page, Approve plan is enabled at once; press it. At the runner's next pick the ADR is accepted, then the plan approved and its tickets queued.
- Reply on a thread: it leaves "Your answers wanted" at once and shows in Coming only.
