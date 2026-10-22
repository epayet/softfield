# ADR 34: A card may use Claude's reserve

- **Status:** Accepted (by the owner, 2026-10-22)
- **Date:** 2026-10-22
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 15](15-allowance-aware-routing.md) item 5 (who may dip into the week's reserve) and [ADR 22](22-one-visible-queue.md) item 4 (the switches). The two 24-hour switches stay as they are.
- **Evidence:** F172 (owner, 2026-10-22): "i currently set the reserve on because there are some tickets i really want, but i'm keeping an eye on when to turn it off again once the tickets i want are on". On that day both switches were on until Fri 09:35 with the week at 67% and its mark at 70%: the switch lets every lead ticket past the mark, not only the ones wanted, and it has no idea when they are done.

## Context
- Past the week's mark (70%), a lead ticket parks and waits for the owner (`at_reserve`, `runner/loop.py`); support jobs (checkpoints, escalations, reviews, planner jobs) always may use the reserve (ADR 15 item 4).
- The week's switch is all or nothing and lasts 24 hours. The owner thinks in cards (the board, the planning room), not in tickets: F171 alone has four.
- A card's header already carries what the runner needs to know about it (`**State:** ready · **Priority:** 2 · **Area:** factory`), and the runner already rewrites it at the owner's request (the board's order).
- Developer tickets need no Claude; the reserve only ever holds lead tickets.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ A card may be marked "may use Claude's reserve".** The owner marks or unmarks it from the card's page; the board shows the mark. It is written in the card's header as `**Reserve:** yes`, by the runner, like its priority.
2. **The mark is a `reserve` request** (ADR 18), with the card's short key as its subject (`f142`) and `on` or `off`, beside the switches' `week` and `five_hour`. No new kind; the dashboard's write stays as it is.
3. **⚑ A marked card's lead tickets run as if both switches were on** (the week's reserve and the owner's 25% of the 5-hour window), and so do the lead tickets they wait for (`depends_on`, all the way down, whatever their card): marking F108 must not leave it waiting behind F75's lead ticket parked at the reserve. Every other lead ticket parks as today.
4. **No timer: the mark ends with the work.** Once the card has no ready ticket left it lets nothing run, and the runner removes it from the header at sign-off. Turning it off earlier is the same lever.
5. **⚑ Both reserves** (owner, 2026-10-22: "this is more important than anything else so use all reserve for it"). A marked card's ticket also takes the owner's 25% of the 5-hour window; other tickets still wait there for its switch or its reset. The mark says nothing about order: the card's priority on the board still decides which ticket goes first.
6. **Order at the reserve:** developer tickets, then the marked cards' lead tickets (and what they wait for) by priority; a lead ticket parks only when none of these can run, as ADR 15 item 5 says today.
7. **Only the owner marks a card.** A planner or lead job never writes `**Reserve:**`.
8. **Marked, a parked ticket goes at once:** a ticket of the card already parked at either reserve is retried at the next pick, and its Needs-you item goes.

## Settled with the owner
- **Both reserves, not the week's only** (2026-10-22): the mark means "this card matters more than anything else", so its tickets use the week's reserve and the owner's 5-hour share alike (item 5).

## Alternatives turned down
- **Mark each ticket:** the owner would mark F171's four tickets one by one, and a replan that adds a ticket would leave it out.
- **Cards with priority 1 or 2 use the reserve:** no new lever, but dragging a card up on the board would spend the reserve without saying so, and three cards share priority 1 today.
- **A switch that turns itself off when the queue's top N tickets are done:** the owner would still count tickets.

## Consequences
- The owner can leave both switches off and mark the two or three cards they want; nothing needs watching.
- **Risk:** every marked card draws on the reserve kept for reviews, checkpoints and planner jobs, and on the 5-hour room the owner keeps for their own sessions. Mark many and a window can run to 100%, when Claude stops for everything, the owner's planning and terminal sessions too, until the reset. The switches have the same risk today; the Overview lists the marked cards under Claude's meters so it is seen.
- `Card` (`runner/milestone.py`) gains `reserve: bool`; `_next_task`, `at_reserve`, `at_five_hour` and `_waits_for_the_owner` take the marked set.
