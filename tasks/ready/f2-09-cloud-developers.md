---
id: f2-09-cloud-developers
milestone: f2
depends_on: [f2-02-claude-window, f2-06-overview-allowances, f2-13-overview-allowances-fixes, f2-07-agents-models]
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
The cloud developers' roles and ratings follow what they actually did in F2, so developer tickets keep going to the cloud first and local is the floor.

### Context
Read `docs/adr/15-allowance-aware-routing.md` items 6 and 7 (Ollama "is one more developer while it has allowance, until the bench says otherwise"), `docs/milestones/f2.md` ("Before go", item 2: the owner's bench), `runner/bench.py` and `workflow/runner.toml` (`[agents.ollama-*]`, `[roles]`).
- **Already done (owner, 2026-10-02):** `ollama-gpt-oss-120b` and `ollama-nemotron-3-super` joined `[roles] developer` before any valid bench (ADR 15 item 7 allows it). The 2026-10-02 bench doesn't count: its agents edited the main checkout (f2-12).
- **The evidence:** F2's developer jobs (role `developer` or `last-attempt`, agent `ollama-*`) in the metrics database (`~/.local/share/software-factory/factory-metrics.sqlite`; read it with `uv run python` and `sqlite3` in read-only mode, `file:…?mode=ro`): first-attempt passes, attempts, minutes, refusals and their resets (how much Ollama allowance a ticket costs), against the local model's F1 numbers in `docs/reviews/factory-f1.md`.
- **Change only what the evidence supports:** an agent that passed its tickets keeps its place and its `rating` moves to what its results show (ADR 15 item 9's scale); one that failed or was refused at once leaves `[roles] developer`, with the reason in a comment. With no Ollama jobs at all in F2, change nothing and say why.
- Record the results as a dated entry in ADR 14's probe section, and update lead.md's "Known range".

### Done when
- `[roles] developer` and the ratings match F2's evidence, and `tests/runner/test_config.py` passes
- ADR 14, lead.md's Known range and F2's doc record the numbers
- `uv run runner check-all --task f2-09-cloud-developers` passes
