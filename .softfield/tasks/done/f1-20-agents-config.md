---
id: f1-20-agents-config
milestone: f1
depends_on: [f1-19-replan-agents, f1-47-build-on-and-finish]
agent: lead
difficulty: 7
files:
  - runner/agents.py
  - runner/config.py
  - runner/claude.py
  - runner/loop.py
  - runner/milestone.py
  - workflow/runner.toml
tests:
  - tests/runner/test_agents.py
  - tests/runner/test_config.py
  - tests/runner/test_claude.py
---

### Goal
Agents and roles are declared in `workflow/runner.toml`, every job is a neutral spec, and `runner/claude.py` is the first adapter that runs one.

### Context
Read `docs/adr/14-developers-and-agents.md` items 2–4 and 11, its probe results, and `docs/adr/15-allowance-aware-routing.md` items 2, 6, 9 and 12, which amend it. Test-first.
- **Config:** `[agents.<id>]` with `harness`, `model`, and `rating = <1–10>` (one rating, ADR 15 item 9), and optional seeds for its windows (`windows = [...]`, ADR 15 item 2); `[roles]` mapping each ADR 14 role to a list of agent ids. Ids and models follow D6 in `docs/milestones/f1.md` (f1-21 and f1-22 declare the Ollama and Copilot agents). f1 keeps today's assignment: local Qwen for `developer` and `last-attempt`, `claude-opus` for `direction`, `escalation`, `lead-ticket` and `review`, `claude-sonnet` for `checkpoint`. `[claude] checkpoint_model` goes, replaced by the role. A role naming an undeclared agent is a config error.
- **`runner/agents.py`:** the `JobSpec` (role, prompt, read-only or edit globs, allowed commands, timeout), the `JobResult` (ok, text, duration, usage: tokens or requests, cost, and a refusal with its reset if any), and the adapter protocol: `run(agent, spec, repo, log_path, now) -> JobResult`. A registry maps a harness name to its adapter.
- **Claude adapter:** `runner/claude.py` translates the spec (edit globs → `Edit(<glob>)`, commands → `Bash(<prefix>:*)`, the shell note) and maps errors to ADR 15 item 12's classes: `limit(window, resets_at)`, `transient` or `failure`, keeping the waits already on main (`TRANSIENT_WAITS`, the fixed retry for a limit with no time) and f1-44's readings. Its callers in `runner/loop.py` and `runner/milestone.py` build specs by role, and every job records the agent id that ran it.
- `[roles] developer` may list `claude-sonnet` and `claude-opus` after local (ADR 15 item 6), but f1 keeps them out until f1-25 routes by allowance.
- Behaviour stays the same: the loop tests pass unchanged, apart from how they fake the adapter.

### Done when
- the config loads the agents and roles above, and refuses a role naming an unknown agent
- a spec with edit globs and commands becomes the same `--allowedTools` as today's jobs
- a Claude usage-limit message comes back as a refusal with its reset time
- each job row carries the agent id its role resolved to
- `uv run runner check-all --task f1-20-agents-config` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
