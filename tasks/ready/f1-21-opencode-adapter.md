---
id: f1-21-opencode-adapter
milestone: f1
depends_on: [f1-20-agents-config]
agent: lead
difficulty: 6
files:
  - runner/local_model.py
  - runner/agents.py
  - runner/loop.py
  - opencode.json
  - workflow/runner.toml
tests:
  - tests/runner/test_local_model.py
  - tests/runner/test_loop.py
---

### Goal
OpenCode is an adapter like Claude's, so a developer job can run on the local model or on an Ollama Cloud model by configuration alone.

### Context
Read `docs/adr/14-developers-and-agents.md` items 2–4 and 10, its probe results, and `runner/agents.py`. Test-first, with the probe's fixture in `tests/runner/fixtures/probes/`.
- `runner/local_model.py`'s `run_opencode` becomes the `opencode` harness's adapter: the agent's `model` picks the provider (LM Studio or Ollama, both in `opencode.json`); tokens, steps, peak context, streak and refused commands come back in the `JobResult`, as they do today.
- The LM Studio warm-up and loaded-context checks apply only to the local provider.
- **Refusals:** an Ollama quota or limit error (its shape is in the probe results) ends the job as a refusal with its reset, if the message gives one; it isn't a failed attempt.
- Declare the Ollama models the probes confirmed as agents in `workflow/runner.toml`, each with a starting rating from ADR 14's size comparison (item 7), and in no role yet.

### Done when
- a developer job on the local agent behaves as before (the loop tests pass)
- the same job on a fake Ollama agent runs `opencode run` with that model and skips the warm-up
- the probe's refusal text gives a refusal, not a failed attempt
- `uv run runner check-all --task f1-21-opencode-adapter` passes
