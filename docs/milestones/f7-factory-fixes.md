# Milestone F7: factory fixes from 2026-10-04

> **Status: done.** Signed off by the owner on 2026-10-06. Base: git tag `f7-factory-fixes-start`. Report: [`docs/reviews/f7-factory-fixes.md`](../reviews/f7-factory-fixes.md).
> From the 2026-10-04 session: [ADR 24](../adr/24-ratings-that-hold.md) (ratings that hold, Accepted) and three runner bugs found while reviewing F3 and F4. Small and urgent: until 01–02 land, gpt-oss-120b gets no first attempt (rated 1).

## Outcome
- Ratings move once per ticket for findings, count bench replays, and start new agents at the floor; today's collapsed ratings are recomputed (Qwen ≈3, gpt-oss-120b ≈2).
- An escalation that implements a ticket commits with its `Task:` trailer.
- Stopping the runner stops the gate it was running.
- `runner signoff` counts a milestone's tickets by their `milestone:`, not their id.
- A bench never touches the main checkout, so the Ollama bench can run again.


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
| 06 | bench-isolation | L | 5 | – | a benched OpenCode agent works only in its copy, proven by a canary |

## Replay log
`uv run runner ratings --replay`, 2026-10-04, on the real metrics database (f7-02).
- **What it plays:** every rated ticket's game, every judged verdict and every bench run, in time order, from each agent's estimate.
- **Findings, per ADR 24 item 1:** findings on a merged ticket's code re-play that ticket's game a quarter lower, at the game's own time.
  - That's 16 of Qwen's 19 merged tickets, and 5 of gpt-oss-120b's 7.
  - Charging the quarters at the review's time instead, as the first run of the code did, still takes Qwen to 1.00: 16 quarters at the end, with no games after them to correct it.
- **Benches:** they were never rated before ADR 24, so the replay plays them from their jobs.

| Agent | Before | After | Coding games |
|---|---|---|---|
| local-qwen3.6-35b-a3b | 1.00 | **2.52** | 33 |
| ollama-gpt-oss-120b | 1.00 | 1.00 | 16 |
| ollama-gemma4-31b | 5.00 | 2.11 | 2 (benches) |
| ollama-nemotron-3-super | 4.32 | 2.73 | 1 (bench) |
| claude-opus | 10.00 | 10.00 | 53 |
| copilot-auto | 8.46 | 8.46 | 0 (reviews only) |
| ollama-nemotron-3-ultra | 6.00 | 6.00 | 0 |
| claude-sonnet | 5.67 | 5.67 | 3 |
| ollama-gpt-oss-20b | 4.00 | 4.00 | 0 |
| ollama-nemotron-3-nano-30b | 4.00 | 4.00 | 0 |

- **Against ADR 24's Consequences:**
  - Qwen ends at 2.52, short of ≈3: it lost 14 of its 33 tickets.
  - **gpt-oss-120b stays at 1.00, not ≈2.** It lost three benches (f1-36, f1-38, f4-25) and six tickets, against seven merges.
  - The untested Ollama models route at the floor (fewer than 3 games), as expected.
- **For the owner:** gpt-oss-120b still gets no first attempt.
- **Rows written:** only for agents whose rating moved. A second run wrote nothing.

## Bench isolation probe
f7-06, 2026-10-05: a real `opencode run` (`ollama/gpt-oss:20b-cloud`) in a bench copy made by `make_copy`, asked to write a file by a relative path.
- **The cause was `PWD`.** OpenCode takes its directory from `PWD` over its real cwd. The runner, started in the main checkout, passed its own `PWD` on.
  - With `PWD` naming the main checkout, the write landed in the main checkout, not the copy.
  - With `PWD` naming the copy, it landed in the copy.
  - So neither the clone (f2-12) nor the new root commit (f4-19) could have helped.
- **The fix:** `runner/procs.py`'s `run_streaming` sets `PWD` to the cwd it starts a job in. Re-probed through `run_opencode` from the main checkout: the file landed only in the copy, and the main checkout's status didn't change.
- **The canary:** `runner bench` compares the main checkout's `git status --porcelain` before and after each replay. A change stops the bench, names the files, and voids the replay: its jobs get outcome `void`, and it's no rating game.
- **For the owner:** every OpenCode bench before this fix probably ran in the main checkout. That includes 2026-10-04's (f4-25: gemma4, gpt-oss-120b, nemotron-3-super), and those runs feed the replay log above. Suggested fix: a ticket that sets those bench jobs to `void`, then reruns `runner ratings --replay`.

## Void benches
`uv run runner ratings --void-benches-before 2026-10-05T00:59:54+01:00 --replay`, 2026-10-05, on the real metrics database (f7-07). It voided 19 OpenCode ticket-bench jobs, then recomputed.

| Agent | Jobs voided | Before | After | Coding games after |
|---|---|---|---|---|
| ollama-gpt-oss-120b | 9 (its three lost benches, 3 attempts each) | 1.00 | **1.43** | 13 |
| ollama-gemma4-31b | 6 | 2.11 | **5.00** (its estimate) | 0 |
| ollama-nemotron-3-super | 2 | 2.73 | 2.73 | 1 |
| ollama-nemotron-3-ultra | 2 | 6.00 | 6.00 | 0 |

No other agent moved, and none has a game left from a void bench.
- **gpt-oss-120b ends at 1.43, not ≈2.** Without the benches it still lost six tickets against seven merges, five of those merges with findings.
- **nemotron-3-super's game is f2-07,** the real ticket it blocked on twice, not a bench: its benches were interrupted, so never games. The replay log's "1 (bench)" above was wrong. It stays at 2.73.
- **Every Ollama model now routes at the floor** (fewer than 3 games), except gpt-oss-120b at 1.43. Suggested next step, as the review says: a clean Ollama bench on 3–4 small finished tickets, the first valid bench games.

