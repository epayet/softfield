---
id: f9-16-no-ollama-allowance
milestone: f9-line-polish
depends_on: []
difficulty: 2
files:
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's agent allowance shows Claude's and Copilot's windows only: the Ollama row, which never has data, goes.

### Context
Read `agent_allowances` in `factory_dashboard/overview.py` (the `ollama` group) and the allowance tests in `tests/factory_dashboard/test_overview.py` (the expected rows include "Ollama allowance no data yet").
- The owner (2026-10-06): "remove ollama allowance, if there is no data it's useless". Ollama has no usage API; a refusal stays the only signal (ADR 15 item 2), and the runner keeps handling it.
- Only the dashboard row goes; the floor's "Ollama cloud" machine stays.

### Done when
- `/`'s allowance panel has Claude's 5-hour window, Claude's week and Copilot's month, and no Ollama row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
