---
id: f1-27-bench
milestone: f1
depends_on: [f1-25-router]
agent: lead
difficulty: 7
files:
  - runner/bench.py
  - runner/cli.py
tests:
  - tests/runner/test_bench.py
---

### Goal
`uv run runner bench <ticket…> --agents <id…>` replays finished tickets for chosen agents, in identical conditions, and records the results.

### Context
Read `docs/adr/14-developers-and-agents.md` item 8. Test-first, with a fake adapter and a small repo in `tmp_path` (`tests/runner/conftest.py` has one).
- For each ticket × agent: a throwaway worktree in `var/bench/` from the parent of the ticket's merge commit, with today's workflow files overlaid (`AGENTS.md`, `docs/agents/`, `opencode.json`, `workflow/`), the ticket copied back into `tasks/ready/`, then the usual attempts and gates with that agent. **No Claude:** a failed last attempt is recorded as "would escalate".
- Jobs have role `bench` and never touch `main`, `tasks/` or the real branches; the worktree is removed afterwards.
- **Facts (f1-07):** every job row needs a run (`jobs.run_id` is required; `runs` is keyed by project and `run_dir`). A job row's key is (run, ticket, role, attempt), without the agent, and `metrics.start_job` on an existing key restarts that row: two agents benched on one ticket in one run need different keys.
- It stops at the first refusal and says which agent and when it resets.

### Done when
- a bench of one ticket for two fake agents records two sets of bench jobs, and `main` is unchanged
- the worktree starts at the merge's parent and has today's `AGENTS.md`
- a failing agent ends with "would escalate", without calling Claude
- a refusal stops the bench with its reset
- `uv run runner check-all --task f1-27-bench` passes
