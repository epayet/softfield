---
id: f1-25-router
milestone: f1
depends_on: [f1-21-opencode-adapter, f1-22-copilot-adapter, f1-24-ratings]
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
Read `docs/adr/14-developers-and-agents.md` items 9–11 and its probe results. Test-first with table tests; the router is pure (candidates, ratings, costs, forecasts and the time are parameters).
- **`route(role, ticket, attempt, candidates, …) -> (agent, reason)`:** the cheapest candidate whose coding rating covers the difficulty (local is cheapest); harder tickets and last attempts go to the best-rated cloud candidate that isn't refusing; when a service's forecast says it will reset with credit unused, it also takes ordinary tickets. Lead-only work (`agent: lead`, protected paths) never routes to a developer. The reason is one plain line, stored in `jobs.routing_reason`.
- **`forecast(agent, usage_events, jobs, now)`:** when an agent is likely to run out and when it resets, learned from its past refusals and resets when no API answers. The dashboard shows it later (f1-30).
- **Refusals (item 10):** a refused attempt doesn't count; the loop records it and reruns the attempt on the next candidate. Local never refuses, so work never stops.
- **Facts (f1-07):** `metrics.start_job` already takes `routing_reason`, and D2 has every column this needs. A job row's key is (run, ticket, role, attempt), without the agent, and `start_job` on an existing key restarts that row: the loop's `attempt` column is `next_number`'s count of the ticket's jobs in the session, not the attempt the ticket is on. The runner writes only `usage_events` of kind `refusal` so far.
- **f1 keeps `[roles]` as it is,** so in practice every job still routes to local and Claude; the tests use fake cloud candidates.

### Done when
- table tests cover: an easy ticket to local; a hard one to cloud; a last attempt to cloud; a refusing cloud agent skipped; leftover credit taking an ordinary ticket; a lead ticket never routed
- in the loop, a fake cloud agent's refusal reruns the same attempt on local, and the attempt count doesn't grow
- each job row has its routing reason
- `uv run runner check-all --task f1-25-router` passes
