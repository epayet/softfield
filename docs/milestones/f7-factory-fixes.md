# Milestone F7: factory fixes from 2026-10-04

> **Status: planned** (2026-10-04, with the owner). **State:** ready · **Priority:** 1 · **Area:** factory
> From the 2026-10-04 session: [ADR 24](../adr/24-ratings-that-hold.md) (ratings that hold, Accepted) and three runner bugs found while reviewing F3 and F4. Small and urgent: until 01–02 land, gpt-oss-120b gets no first attempt (rated 1).

## Outcome
- Ratings move once per ticket for findings, count bench replays, and start new agents at the floor; today's collapsed ratings are recomputed (Qwen ≈3, gpt-oss-120b ≈2).
- An escalation that implements a ticket commits with its `Task:` trailer.
- Stopping the runner stops the gate it was running.
- `runner signoff` counts a milestone's tickets by their `milestone:`, not their id.


## Decisions
- **D1 The finding penalty** (ADR 24 item 1): once per ticket, only for the agent that merged it, −0.25 × K with nothing expected. Elo's step is linear in the result, so this equals re-playing the ticket's game 0.25 lower. A ticket not merged costs nothing more.
- **D2 Bench games** (item 3): a `bench` job's ticket is a game for its agent, labelled `bench <result>` so it never collides with the real ticket's labels; played once per (agent, ticket, bench run).
- **D3 The floor** (item 3, settled with the owner): for routing, an agent with fewer than 3 rated coding games reads 1, whatever its estimate.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | ratings-rules | L | 5 | – | D1–D3 in `runner/ratings.py` and `runner/loop.py` |
| 02 | ratings-replay | L | 3 | 01 | `runner ratings --replay` recomputes every agent under ADR 24; run it, log before/after here |
| 03 | escalation-task-trailer | L | 2 | – | `implemented` escalations commit with `Task:` |
| 04 | gates-stop-with-runner | L | 3 | – | the runner's exit kills its running gate's process group |
| 05 | signoff-by-milestone | L | 2 | – | `signoff` and `_ids` read `milestone:` |

