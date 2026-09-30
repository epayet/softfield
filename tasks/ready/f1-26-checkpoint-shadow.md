---
id: f1-26-checkpoint-shadow
milestone: f1
depends_on: [f1-22-copilot-adapter, f1-23-findings-json]
agent: lead
difficulty: 5
files:
  - runner/loop.py
  - runner/prompts.py
  - workflow/runner.toml
  - factory_dashboard/queries.py
tests:
  - tests/runner/test_loop.py
  - tests/factory_dashboard/test_queries.py
---

### Goal
A `checkpoint-shadow` agent reviews the same merges as each checkpoint; its findings are recorded and never acted on.

### Context
Read `docs/adr/14-developers-and-agents.md` item 12 and its probe results. Test-first.
- After each checkpoint, every agent in `[roles] checkpoint-shadow` gets a read-only spec over the same merges, asking for the same findings JSON as the checkpoint (f1-23), in one short prompt (Copilot Free allows 50 requests a month). Its findings are stored on its own job with role `checkpoint-shadow`. It edits nothing: its spec has no edit globs.
- A shadow's refusal or error is recorded and the run carries on.
- `[roles] checkpoint-shadow` names the Copilot agent from f1-22, so M5's checkpoints are shadowed.
- **Eligibility (item 12)** as a query in `factory_dashboard/queries.py`: per agent and role, whether it meets the starting bars (checkpoint: reviewing ≥ 8 over 2+ milestones, no missed blocking finding, coding ≥ the difficulty of the tickets it reviewed), with the reason when not.

### Done when
- a checkpoint with a shadow configured leaves two jobs and two sets of findings, and only the checkpoint's changes reach the repo
- a shadow that refuses leaves a refused job and doesn't stop the run
- eligibility says no with its reason for an agent with one milestone, and yes for one meeting every bar (fixture ratings)
- `uv run runner check-all --task f1-26-checkpoint-shadow` passes
