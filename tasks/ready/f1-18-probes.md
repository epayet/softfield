---
id: f1-18-probes
milestone: f1
depends_on: [f1-17-difficulty]
agent: lead
difficulty: 5
commands:
  - ollama list
  - ollama ps
  - ollama show
  - ollama run
  - opencode run
  - opencode models
  - copilot --help
  - copilot -p
  - gh auth status
  - gh api
files:
  - docs/adr/14-developers-and-agents.md
  - opencode.json
  - tests/runner/fixtures/probes/
tests:
  - tests/runner/test_local_model.py
---

### Goal
Find the facts the agent tickets need about Ollama Cloud and the Copilot CLI, and record them in ADR 14.

### Context
Read `docs/adr/14-developers-and-agents.md` (Context and "Probes before the code"). You may run only the commands this ticket lists, one per Bash call.
- **Ollama:** which cloud model tags `ollama` offers (`ollama show`, a one-line `ollama run <tag> "Say hi"`); add an Ollama provider for its cloud models to `opencode.json` beside LM Studio's, and do one small `opencode run` on a cloud model, saving its JSON log as `tests/runner/fixtures/probes/opencode-ollama.jsonl`. What a refusal (a quota or limit error) looks like, if you can see one or its documentation; what the run cost of the allowance, if anything shows it.
- **Copilot:** its flags (`copilot --help`: model choice, `--allow-tool`, `--deny-tool`, non-interactive output), the models Free offers, and one read-only review prompt with `copilot -p`, saved as `tests/runner/fixtures/probes/copilot-review.txt`. **At most 3 Copilot prompts: Free has 50 requests a month.** Never allow it shell or write tools.
- **Billing:** whether `gh api /users/{user}/settings/billing/...` answers on Free (`gh auth status` gives the user).
- A missing login (`ollama signin`, Copilot, `gh`) is a fact to record, not a failure: note what the owner must run, and carry on with the rest.
- **Not here:** Claude's usage endpoint (it would mean reading the OAuth token in a headless job).
- Record everything as a dated "Probe results" section at the end of ADR 14: facts only, with the exact commands, tags and flags.

### Done when
- ADR 14 has "Probe results" covering Ollama, Copilot and billing, each fact or "not probed: <why>"
- a test in `tests/runner/test_local_model.py` reads the Ollama fixture with `parse_events` and gets non-zero tokens (skip nothing: without a fixture, say so in the ADR and test LM Studio's shape instead)
- `uv run runner check-all --task f1-18-probes` passes
