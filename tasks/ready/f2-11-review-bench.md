---
id: f2-11-review-bench
milestone: f2
depends_on: [f2-02-claude-window, f2-12-bench-isolation]
agent: lead
difficulty: 7
files:
  - runner/bench.py
  - runner/cli.py
  - factory_dashboard/queries.py
  - factory_dashboard/eligibility.py
  - docs/workflow.md
tests:
  - tests/runner/test_bench.py
  - tests/factory_dashboard/test_eligibility.py
---

### Goal
`runner bench --review` replays past checkpoints for an agent and scores its findings against the known ones, so an agent earns a reviewing role from bench results instead of shadowing.

### Context
Read `docs/adr/16-claude-window-and-named-milestones.md` item 10, `docs/adr/14-developers-and-agents.md` item 12 (the bars), `runner/bench.py` (worktrees, `ROLE`, `BenchResult`), the checkpoint's prompt and findings JSON (`runner/prompts.py`, `runner/review.py`, f1-23), `runner/copilot.py` (the read-only adapter), and `factory_dashboard/queries.py` (`eligibility`) with `factory_dashboard/eligibility.py`. Test-first.
- **What to replay:** a checkpoint job (role `checkpoint`, no ticket) and the merges it reviewed. Its known findings are the `findings` rows of that job, plus later ones on the same tickets (a review's, or a fix ticket's `finding:`). F1 has 10 checkpoints (`runner report f1`); M3's and M4's review findings are known per ticket.
- **Scoring:** a known finding the agent also reports (same file, overlapping lines or the same summary) is a hit; one it misses is a miss, and a missed blocking one is recorded as such (ADR 14's bar). A finding nobody knew is listed for the lead to judge, not scored. Each replay is a job of role `bench` with the score in its `note`.
- **Eligibility:** the Agents page's panel reads review-bench results instead of shadow jobs (`SHADOW_SUFFIX`); the bars stay ADR 14 item 12's, with "2+ milestones" read as "replays from 2+ milestones".
- Copilot's normal use is paced by its month (ADR 15 item 1); a bench stops at its first refusal, as now.
- `[roles] checkpoint-shadow` is already empty (`workflow/runner.toml`); leave the shadow's code in place.

### Done when
- a review replay of a fixture checkpoint with two known findings scores an agent that reports one of them as 1 hit, 1 miss, and lists its extra finding unscored
- the eligibility panel shows an agent eligible from review-bench results alone
- `uv run runner check-all --task f2-11-review-bench` passes
