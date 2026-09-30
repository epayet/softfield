---
id: f1-22-copilot-adapter
milestone: f1
depends_on: [f1-20-agents-config]
agent: lead
difficulty: 6
files:
  - runner/copilot.py
  - runner/agents.py
  - workflow/runner.toml
tests:
  - tests/runner/test_copilot.py
---

### Goal
`runner/copilot.py` runs a job spec through the Copilot CLI, for read-only review jobs.

### Context
Read `docs/adr/14-developers-and-agents.md` items 2–4 and 10, its probe results (flags, models, output), and `runner/agents.py`. Test-first, with the probe's fixture `tests/runner/fixtures/probes/copilot-review.txt`; tests fake the subprocess, never call Copilot.
- The spec becomes `copilot -p` with the model and `--allow-tool`/`--deny-tool` from its read-only tools; **shell and write tools are always denied**, whatever the spec says.
- The result counts requests (per the probe), parses a quota refusal and its reset, and reads the billing endpoint only if the probe found it answers.
- Declare the Copilot agent (`copilot-<model>`) in `workflow/runner.toml`, in no role yet (f1-26 adds the shadow).

### Done when
- a read-only spec gives the command line with shell and write denied; a spec asking for edits is refused before running
- the fixture's output parses into the result's text and one request
- a quota message gives a refusal
- `uv run runner check-all --task f1-22-copilot-adapter` passes
