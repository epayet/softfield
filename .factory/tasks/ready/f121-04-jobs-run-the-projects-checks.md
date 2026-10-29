---
id: f121-04-jobs-run-the-projects-checks
milestone: f121-projects-not-on-main-or-not
agent: lead
difficulty: 3
depends_on: [f121-02-check-commands-from-project]
files:
  - runner/agents.py
  - runner/loop.py
  - runner/milestone.py
  - runner/bench.py
  - runner/prompts.py
tests:
  - tests/runner/test_agents.py
  - tests/runner/test_prompts.py
---

### Goal
Claude's headless jobs may run the project's own check commands, and their prompts name the project's test command instead of `uv run pytest`.

### Context
Read D6 in `.factory/cards/f121-projects-not-on-main-or-not.md`, then `CHECK_COMMANDS` in `runner/agents.py` and where `runner/loop.py`, `runner/milestone.py` and `runner/bench.py` pass it as `commands=`, and the two `uv run pytest -q {tests}` lines in `runner/prompts.py`.
- `CHECK_COMMANDS` becomes a function of the project's `Checks` (from f121-02): the first words of each `lint`, `fix` and `test` command as Bash prefixes (`uv run ruff`, `npx vitest`), `uv run mypy` when `mypy` has targets, and `softfield check-all` always. Duplicates go.
- With the defaults, the prefixes include today's four.
- The prompts show the project's `test` command joined with spaces, then the ticket's tests.

### Done when
- with no new keys, a lead ticket's job may run `uv run pytest`, `uv run ruff`, `uv run mypy` and `softfield check-all`, as today
- with `test = ["npx", "vitest", "run"]`, the job may run `npx vitest run` and its prompt says `npx vitest run <the ticket's tests>`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
