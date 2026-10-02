---
id: f1-25-router
milestone: f1
depends_on: [f1-21-opencode-adapter, f1-22-copilot-adapter, f1-24-ratings, f1-43-allowance]
agent: lead
difficulty: 8
files:
  - runner/router.py
  - runner/loop.py
  - runner/metrics.py
tests:
  - tests/runner/test_router.py
  - tests/runner/test_loop.py
---

### Goal
`runner/router.py` picks the agent for each developer job, and the loop follows it, falling through to the next candidate on a refusal.

### Context
Read `docs/adr/15-allowance-aware-routing.md` items 1, 5–7 and 9 (they replace ADR 14 item 9), `docs/adr/14-developers-and-agents.md` items 10–11 and its probe results, and `runner/allowance.py` (f1-43). Test-first with table tests; the router is pure (candidates, ratings, costs, readings and the time are parameters).
- **`route(role, ticket, attempt, candidates, …) -> (agent, reason)`:** **cloud first, paced** (ADR 15 item 6): the best-rated candidate that covers the difficulty and that `runner/allowance.py` permits now, else local. It is called when the ticket is picked, and again for each attempt. **Step up** (item 7): after a failed attempt, the cheapest permitted candidate rated at least 2 points above the one that failed, else the same agent again. The checkpoint after a cloud developer's merge goes to a model different from it (item 9). Lead-only work (`agent: lead`, protected paths) never routes to a developer. The reason is one plain line, stored in `jobs.routing_reason`.
- **No separate forecast:** `runner/allowance.py` holds the windows and the pace; the dashboard (f1-30) reads it.
- **Refusals (item 10):** a refused attempt doesn't count; the loop records it and reruns the attempt on the next candidate. Local never refuses, so work never stops.
- **Facts (f1-07):** `metrics.start_job` already takes `routing_reason`, and D2 has every column this needs. A job row's key is (run, ticket, role, attempt), without the agent, and `start_job` on an existing key restarts that row: the loop's `attempt` column is `next_number`'s count of the ticket's jobs in the session, not the attempt the ticket is on.
- **What each agent's allowance is known from (f1-18's probes):** Claude's windows from f1-44's readings (`usage_events` kind `reading`, per `window`, `value` 0–1); `copilot-auto`'s month from f1-22's reading, but it is read-only and never a developer; the Ollama agents (f1-21) have no reading and no known refusal shape, only our own token counts and the refusals f1-21 records, so they start at unknown capacity (ADR 15 item 2). The runner writes refusals as kind `refusal`.
- **Turn it on:** add `claude-sonnet` to `[roles] developer` after local. The reserve and the reserve question (f1-46) protect lead work. The tests use fake candidates and readings.

### Done when
- table tests cover: cloud within its pace; local when the pace is spent; the sweep taking an ordinary ticket; a step up of 2+ points after a failure and none for 1 point; a refusing cloud agent skipped; a lead ticket never routed; the checkpoint after Sonnet's merge not going to Sonnet
- in the loop, a fake cloud agent's refusal reruns the same attempt on local, and the attempt count doesn't grow
- each job row has its routing reason
- `uv run runner check-all --task f1-25-router` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
