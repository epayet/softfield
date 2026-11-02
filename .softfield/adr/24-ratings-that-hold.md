# ADR 24: Ratings that hold: one finding penalty per ticket, and the bench counts

- **Status:** Accepted (by the owner, 2026-10-04)
- **Date:** 2026-10-04
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 14](14-developers-and-agents.md) items 6–7 and [ADR 15](15-allowance-aware-routing.md) item 9 (how ratings move); [ADR 16](16-claude-window-and-named-milestones.md) item 10 (what the bench is for).
- **Evidence:** `rating_changes` in the metrics database, 2026-10-04 (`runner/ratings.py`).

## Context
- **Routing reads one rating per agent.** A developer gets a ticket's first attempt only when its rating is at least the ticket's difficulty (`runner/router.py` `_first_pick`), with the local model as the floor.
- **The ratings collapsed on 2026-10-04:**
  - **Qwen:** its ticket games held it at about 3 all week (+0.11 net over 63 changes). Then the F3 and F4 reviews' verdicts took **−4.11** in one evening, and it sits at the floor, **1.0**.
  - **gpt-oss-120b:** fell from 2.2 to **1.0** the same way. It now gets no first attempt at all, though it finished 6 of its 13 real tickets itself.
  - **The cause:** `judged_games` charges the author −0.25 × K for *every* confirmed or missed finding on a ticket's code, with nothing expected. A review confirms many findings, often several per ticket and often checkpoint findings re-counted. A ticket merged first time with four findings scores below a ticket the agent never merged.
- **The bench moves no rating.** `runner bench` records `bench` jobs that the Agents page's eligibility reads, but `runner/ratings.py` never plays them. A model added after a bench keeps its guessed estimate: nemotron-3-ultra's 6 and gemma4's 5 would outrank every proven developer on day one.

## Decisions (draft; ⚑ = deviates from an earlier decision)
1. **⚑ One finding penalty per ticket, inside its game.**
   - A merged ticket whose code the final review confirms (or marks missed) any finding on scores 0.25 less: 0.75 merged first, 0.25 merged later. It is never below a ticket not merged (0).
   - The change re-plays that ticket's one game with the lower result. It is not an extra penalty with nothing expected.
   - The number of findings on a ticket no longer matters to the rating. The review report still lists them all.
2. **Reviewers' games are unchanged:** a confirmed finding is a win for its reviewer, a rejected or missed one a loss, against the reviewed ticket's difficulty.
3. **⚑ Bench replays count:** a benched ticket is a game like a real one (first attempt 1, a later one 0.5, none 0), at that ticket's difficulty. This is how a new model earns a rating before the router trusts it: an agent with fewer than 3 games keeps the floor (1), not its estimate, for first attempts.
4. **A one-off recompute:** `runner ratings --replay` re-plays every agent's games from the start under these rules and writes the result as new `rating_changes` rows, labelled `replay ADR 24`, so the history stays.

## Consequences
- **What the recompute should show** (to check against the replay before it's committed):
  - Qwen back to about its game level (≈3);
  - gpt-oss-120b to about 2, so it takes difficulty-2 tickets again;
  - the untested Ollama models at the floor until the bench gives them games.
- Findings still lower an author's rating, but one bad ticket costs one ticket's worth.
- The router stays as it is. Only its inputs become sane.

## Settled with the owner (2026-10-04)
- An agent with fewer than 3 games starts at the floor (1), not its estimate.
- A checkpoint finding the review rejects gives the author nothing back: it never cost them anything.
