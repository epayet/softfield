---
id: f7-07-void-leaked-benches
milestone: f7-factory-fixes
depends_on: []
agent: lead
difficulty: 3
finding: f7-factory-fixes-F1
files:
  - runner/loop.py
  - runner/cli.py
  - docs/milestones/f7-factory-fixes.md
tests:
  - tests/runner/test_loop.py
commands: [uv run runner ratings]
---

### Goal
The bench replays that ran before f7-06's fix, when OpenCode worked in the main checkout, are void and no rating game, and every agent's rating is recomputed without them.

### Context
Read "## Bench isolation probe" and "## Replay log" in `docs/milestones/f7-factory-fixes.md`, `_bench_game`, `_recorded_games` and `replay_ratings` in `runner/loop.py`, `void_replay` and `VOID` in `runner/bench.py`, and the `ratings` command in `runner/cli.py`. Test-first.
- f7-06 found that every OpenCode bench before its fix probably ran in the main checkout. The fix merged as a91d5b5 at 2026-10-05T00:59:54+01:00. Those replays' gates ran in an untouched copy, so their failures say nothing about the agent. Yet the replay log counts them: gpt-oss-120b's three lost benches (f1-36, f1-38, f4-25) keep it at 1.00, against ADR 24's ≈2.
- Add `runner ratings --void-benches-before <ISO time>`. It sets outcome `void` on every `bench` job with a ticket that an agent with `harness = "opencode"` in `workflow/runner.toml` started before that time and that isn't void already. It prints how many jobs it voided, by agent. Jobs of another harness, review benches (no ticket) and later jobs stay as they are. With `--replay` it voids first, then recomputes.
- `_bench_game` already ignores `void`, and a recompute already plays benches from their jobs, so the recompute needs no change.

### Done when
- a test: with OpenCode bench jobs before and after the cut-off and a Claude bench job before it, only the OpenCode ones before it are void, and a recompute then rates the agent without them
- `uv run runner ratings --void-benches-before 2026-10-05T00:59:54+01:00 --replay` has run on the real database. A short "## Void benches" section in `docs/milestones/f7-factory-fixes.md` lists the jobs voided by agent, and each agent's rating before and after.
- `uv run runner check-all --task f7-07-void-leaked-benches` passes
