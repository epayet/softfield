---
id: f153-01-lead-ticket-by-difficulty
milestone: f153-i-wonder-if-sonnet-would-be
depends_on: []
agent: lead
difficulty: 4
area: factory
files:
  - runner/config.py
  - runner/router.py
  - runner/loop.py
tests:
  - tests/runner/test_config.py
  - tests/runner/test_router.py
  - tests/runner/test_loop.py
---

### Goal
With `[roles] lead-ticket` listing two agents and `[claude] lead_first_up_to` set, a lead ticket whose difficulty is at most that number runs on the first agent and the rest on the second, and the ticket's record and the run's report name the agent that did it. With today's config (one agent, no setting) nothing changes.

### Context
Read "What we know" and Decisions D1, D4 and D7 in `.softfield/cards/f153-i-wonder-if-sonnet-would-be.md`, and `.softfield/adr/32-sonnet-on-easier-lead-tickets.md` items 1 and 4. In `runner/config.py`: `Config`, `developer_five_hour_cap` and how it is read from `[claude]`. In `runner/router.py`: `route`, `Ticket` (its `difficulty`), `Route`. In `runner/loop.py`: `run_lead_task`, `_settle_lead_task` (`lead = s.cfg.agent_for(job.role).id`), `_merged_line`, `call_claude` (its `routed` argument, `first_agent`), `candidates`. In `tests/runner/test_router.py`: `test_other_roles_take_their_first_agent`; in `tests/runner/test_loop.py`: `test_a_merged_lead_ticket_is_merged_by_claude` and `test_a_lead_ticket_runs_headless_and_merges_when_check_all_passes`.
- The commit trailer `agent=CLAUDE_HEADLESS_AGENT` stays as it is.
- An interrupted lead ticket resumes on the agent whose session it was (`s.state.interrupted`): don't route it again.

### Done when
- `Config.lead_first_up_to` reads `[claude] lead_first_up_to` (an int, default 0)
- `router.route("lead-ticket", ticket, …)` with two candidates and `lead_first_up_to = 4` gives the first for difficulty 1–4, the second for 5 and up and for no difficulty, each with a one-line reason naming the agent, the difficulty and the limit; with one candidate, or the limit 0, it gives the last candidate listed as today's single-agent config does
- `run_lead_task` passes that route to `call_claude`, and `record_ticket(merged_by=…)` and `_merged_line` name the routed agent
- with `[roles] lead-ticket = ["claude-opus"]` and no setting, the existing lead-ticket tests pass unchanged
- the listed `tests:` pass, and the new tests fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
