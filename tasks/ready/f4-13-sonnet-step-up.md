---
id: f4-13-sonnet-step-up
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 4
files:
  - runner/router.py
  - runner/loop.py
  - workflow/runner.toml
tests:
  - tests/runner/test_router.py
  - tests/runner/test_config.py
---

### Goal
Claude never takes a developer ticket's first attempt; after a failed attempt it may step up, only when no lead work is ready and its 5-hour window is under 30%.

### Context
Read `docs/adr/17-always-on-factory.md` item 1, `runner/router.py` (`route`, `_developer`, `_lead_first`, the step-up), `runner/loop.py` (where `route` gets `lead_ready` and `five_hour_cap`) and `[roles]`/`[claude]` in `workflow/runner.toml`. Test-first.
- Today `claude-sonnet` is off `[roles] developer` (the owner, 2026-10-02), so the step-up can't pick it.
- Add it back to `developer`, after the Ollama agent and before nothing else. In `_developer`, a Claude-harness agent (`CLAUDE`) is never a first pick (attempt 1, or a first pick after a refusal), only a step-up. Set `developer_five_hour_cap = 0.3`, and update the roles pinned in `tests/runner/test_config.py` (`test_the_repos_toml_declares_f1s_agents_and_roles`).
- The routing reason says so, e.g. "claude-sonnet steps up after ollama-gpt-oss-120b failed: no lead work, 5-hour window 12% (under 30%)".

### Done when
- attempt 1 of a difficulty-3 ticket never routes to Sonnet, even when Sonnet is the best rated
- attempt 2 after gpt-oss failed routes to Sonnet at 20% with no lead work, and not at 35% or with a lead ticket ready
- `uv run runner check-all --task f4-13-sonnet-step-up` passes
