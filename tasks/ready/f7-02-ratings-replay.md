---
id: f7-02-ratings-replay
milestone: f7-factory-fixes
depends_on: [f7-01-ratings-rules]
agent: lead
difficulty: 3
files:
  - runner/loop.py
  - runner/cli.py
  - docs/milestones/f7-factory-fixes.md
tests:
  - tests/runner/test_loop.py
commands: [uv run runner ratings]
---

### Goal
`uv run runner ratings --replay` recomputes every agent's rating from its estimate under ADR 24's rules, and the recompute is run once and logged.

### Context
Read item 4 of `docs/adr/24-ratings-that-hold.md`, `replay_ratings` in `runner/loop.py` (today it seeds only the local model, from M1–M4) and the `ratings` command in `runner/cli.py`. Test-first.
- The replay plays every rated ticket's games and verdicts, and every bench replay, in time order, for every agent in `workflow/runner.toml`. It writes new `rating_changes` rows whose `result` starts `replay ADR 24`, after the existing ones, so `standing` reads them as current and the history stays.
- A second replay writes nothing new when nothing changed.

### Done when
- a test: a fixture history with a collapsed rating replays to the game-level rating, and a second replay adds no rows
- the replay has run on the real database, and "## Replay log" in `docs/milestones/f7-factory-fixes.md` lists each agent's rating before and after
- `uv run runner check-all --task f7-02-ratings-replay` passes
