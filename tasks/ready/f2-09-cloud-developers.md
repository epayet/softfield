---
id: f2-09-cloud-developers
milestone: f2
depends_on: [f2-02-claude-window]
agent: lead
difficulty: 5
commands: [uv run runner report]
files:
  - workflow/runner.toml
  - docs/adr/14-developers-and-agents.md
  - docs/milestones/f2.md
  - docs/agents/lead.md
tests:
  - tests/runner/test_config.py
---

### Goal
The Ollama Cloud models that did well on the bench become developers, so developer tickets go to the cloud first and local is the floor.

### Context
Read `docs/adr/15-allowance-aware-routing.md` items 6 and 7 (Ollama "is one more developer while it has allowance, until the bench says otherwise"), `docs/milestones/f2.md` ("Before go", item 2: the owner's bench), `runner/bench.py` and `workflow/runner.toml` (`[agents.ollama-*]`, `[roles]`).
- The bench's results are jobs with role `bench` in the metrics database (`~/.local/share/software-factory/factory-metrics.sqlite`; read it with `uv run python` and `sqlite3` in read-only mode, `file:…?mode=ro`), and under `var/bench/`. The tickets were f1-36 (difficulty 3), f1-12 (4), f1-13 (5) and f1-15 (6); the local model passed 36 and 12 first time, and needed 3 and 5 attempts for 13 and 15.
- For each benched agent: passes per ticket and attempt, minutes, and whether its work merged cleanly. An agent that passes at least the difficulty-3 and -4 tickets first time joins `[roles] developer` ahead of the local model, ordered by results; its `rating` moves to what the results show (ADR 15 item 9's scale). One that fails stays out, with the reason in a comment.
- If no bench rows exist (the owner didn't run it), add only `ollama-gpt-oss-120b` to `[roles] developer` after the local model (so it takes over when local is refused or steps up), and write so in the F2 doc.
- Record the results as a dated entry in ADR 14's probe section, and update lead.md's "Known range".

### Done when
- `[roles] developer` lists the cloud agents the bench supports, with their ratings, and `tests/runner/test_config.py` passes
- ADR 14, lead.md's Known range and F2's doc record the bench's numbers
- `uv run runner check-all --task f2-09-cloud-developers` passes
