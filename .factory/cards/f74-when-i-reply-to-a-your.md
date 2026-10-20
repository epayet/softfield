# Milestone F74: when i reply to a 'your answers wanted' thread, there's a…

> **State:** ready · **Priority:** 5 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
when i reply to a 'your answers wanted' thread, there's a duplicated box in 'coming' of the same thing, and the original box is still in your desk and not orange dotted. the 'coming' part should just have 'coming plants' (or seeds?), while if i answered on a thread it should stay there as orangely dotted if waiting to be picked up the same way with proposals atm

## Why it happens (read from the code, 2026-10-09)
- `coming()` in `factory_dashboard/planning.py` lists a thread when an open `plan_message` request names it, or when the owner's message is its latest and a planner job about it is open.
- `_answers_wanted()` lists a thread whose latest *stored* message is the lead's. The runner stores the owner's message only at its next pick, so until then the thread is in both groups, and `_acted_on()` (which dashes an archive, a sign-off or a seed removal on its way) knows nothing of `plan_message`: the desk box stays solid.
- After the pick, the owner's message is the latest: the thread leaves "Your answers wanted" and only Coming shows it, until the lead's reply brings it back. One conversation jumps between two places.

## Outcome
- **Coming holds only plants** on their way, under the name "Coming seeds": what you just planted, nothing else.
- **A conversation keeps one box, in "Your answers wanted".** From the moment you send a message on a thread until the lead's reply is stored, its box is dashed orange, says when the reply comes ("waiting for the lead · after f63-01, ~12 min"), and no longer counts as waiting for you. Proposals on their way already work this way.
- The first message on a seed, or on an archived thread, shows the same way: its box sits in "Your answers wanted", dashed, at once (a seed leaves "Seeds, not asked about yet").
- "Plant and ask the lead" shows in Coming seeds until the pick, then as a dashed conversation until the lead replies.

## Decisions
- **D1 Coming is plants only.** The thread rows leave `coming()`; the group is named "Coming seeds" (the desk's own word for an idea card, which is what a plant becomes).
- **D2 One conversation, one box.** `_answers_wanted()` also lists a thread with an open `plan_message` request naming it, or whose latest message is the owner's with an open planner job about it (today's Coming rule), whatever its latest stored message and even archived. Those items are `on_its_way`, with the words `waiting for the lead · {next_reply}` that Coming says today (`_next_reply`, `_held`).
- **D3 Until the lead replies, not only until the pick.** The owner's words were "waiting to be picked up"; stopping the dashed box at the pick would make it vanish for the minutes to the hour the lead takes. It goes solid when the lead's reply is stored, as today.
- **D4 A seed with a message on its way leaves Seeds** so it shows once.
- **D5 Counts don't change:** dashed items are already left out of `waiting_for_you` (the tab count, Needs you, F35's arrows).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | one-box-per-conversation | D | 3 | f63-01 | D1–D5 |

Follows `_acted_on` and the proposals' `on_its_way` in the same file: a developer ticket. After f63-01, which reorders the same groups and moves Coming in the same template. F14's f14-02 edits Coming's plant rows; the two don't overlap (F74 removes the thread rows only).

## Done when
- Reply on a thread in "Your answers wanted": on `/planning` its box is dashed orange, "waiting for the lead · …", and nothing about it shows in Coming seeds.
- After the runner's pick, before the lead's reply: the same box, same place, still dashed.
- After the lead's reply: the box is solid again, counted as waiting for you.
- With only a message on its way, there is no Coming seeds section; with a plant on its way, there is, holding just the plant.
