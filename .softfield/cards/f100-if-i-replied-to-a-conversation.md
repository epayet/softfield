# Milestone F100: Proposals show "being revised" while your reply waits for the lead

> **State:** done · **Priority:** 4 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-29. Base: git tag `f100-if-i-replied-to-a-conversation-start`. Report: [`.softfield/reviews/f100-if-i-replied-to-a-conversation.md`](../reviews/f100-if-i-replied-to-a-conversation.md).
> Planted by the owner on 2026-10-10.

## Notes
If I replied to a conversation and it has related plans. It usually means I'm not happy with the proposals yet. On the planning room when that happens (reply to conversation on its way to planner orangery dotted), I want the related proposals to be orangery dotted as well to show that it's being revised. So that it doesn't look like I need to review the plan in the proposal column if I'm still discussing somrthing

## Why it happens (read from the code, 2026-10-27)
- `_open_proposals` in `factory_dashboard/planning.py` dashes a proposal only when the owner's own Approve or Reject on it waits for the runner (`proposal_state` is `on its way`). A message on the thread changes nothing there, so its proposals stay solid and counted in "Proposals to review", the Planning tab and Needs you.
- The thread page's "Proposals from this card" (`_proposals`) and the proposal page (`_standing`) read the same state, so they say `open` too.
- F74 (ready, f74-01) gives the thread itself one dashed box while the owner's message waits for the lead; this card does the same for the thread's proposals.

## Outcome
- **From the moment you send a message on a thread, its open proposals turn dashed orange** wherever they show: "Proposals to review" on the desk, "Proposals from this card" on the thread, and the proposal's own page. They say "being revised · {when the lead replies}", and no longer count as waiting for you.
- **They come back when the lead answers:** the lead's reply lists new proposals (which replace them, F31 D3) or none (the last list stands, solid again).
- **You can still act on them:** Approve and Reject stay on the proposal's page, under a line saying the lead is revising it.
- Mock-up: [`f100-mockup/being-revised.html`](f100-mockup/being-revised.html).

## Decisions
- **D1 One rule for "the lead owes this thread a reply".** f74-01 moves today's Coming rule into `_answers_wanted` (an open `plan_message` request names the card, or the latest message is the owner's or the runner's and an open planner job's subject names it; a cancelled message doesn't count). This card lifts it into one function, `_waiting_for_lead(conn, project_id) -> set[str]` (the cards), which `_answers_wanted`, `_open_proposals`, `_proposals` and `_standing` all read, so the thread and its proposals can't disagree.
- **D2 Only open proposals.** A proposal whose Approve or Reject is already on its way keeps "on its way · the runner applies it at its next pick"; an approved, rejected or replaced one is not listed, as today.
- **D3 Words.** The desk item: `being revised · {next_reply}` (`_next_reply` with `_held` for that thread, as F74's box). The thread page: state `being revised`. The proposal page: a dashed line above the buttons, "Being revised: your message on the thread is on its way to the lead, who may change this draft. You can still approve or reject it as it stands."
- **D4 The buttons stay** (the owner may approve an ADR while still discussing the plan beside it). An approval made then is applied at the runner's next pick as any other; the lead's reply after it sees the proposal approved.
- **D5 At once on the thread page.** Send already redraws `#conversation`; it redraws `#proposals` too, so the aside turns dashed with the message. The desk shows it at its next 5-second poll (you are not on it when you send).
- **D6 Counts follow by themselves:** dashed items are already left out of `waiting_for_you` (the Planning tab, Needs you, F35's arrows) and of the Overview's per-card proposals.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | proposals-being-revised | L | 3 | f74-01 | D1–D6 on the desk, the thread page and the proposal page |

A lead ticket, like f74-01 and f75-01 beside it: it reads `planning.py` and three templates (`runner/instructions/lead.md`, F6: page tickets that must read planning.py are past the local developers). After f74-01, which builds the rule D1 reuses; F75's f75-01 also counts "on its way" proposals for archiving and runs after this one or before it without conflict (a "being revised" proposal is not an Approve on its way).

## Done when
- Send a message on a thread with two open proposals: on `/planning` both are dashed orange under "Proposals to review", "being revised · …", and the Planning tab's count drops by them.
- On the thread page, the aside turns dashed with the message, each proposal saying "being revised".
- On a proposal's page, the "Being revised" line shows above Approve and Reject, which still work.
- After the lead's reply with no proposals: both are solid and counted again; with new proposals, the new ones show solid and the old ones are gone.
- A proposal already approved stays "on its way · the runner applies it at its next pick".
