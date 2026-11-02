---
id: f121-06-a-guide-per-language
milestone: f121-projects-not-on-main-or-not
agent: lead
difficulty: 4
depends_on: [f121-03-what-counts-as-a-test, f121-04-jobs-run-the-projects-checks]
files:
  - docs/agents/stacks/python.md
  - runner/config.py
  - runner/setup.py
  - runner/templates/project.toml
  - runner/templates/project.md
  - runner/templates/opencode.json
  - runner/templates/CLAUDE.md
  - docs/bootstrap.md
tests:
  - tests/runner/test_config.py
  - tests/runner/test_setup.py
---

### Goal
How to write and test code in Python lives in one shared guide, `docs/agents/stacks/python.md`, which every Python project's developers and lead read. A project names its languages in `project.toml` instead of each project writing them out again.

### Context
Read D7 in `.factory/cards/f121-projects-not-on-main-or-not.md`, then `docs/agents/preact.md` (the shape of a guide: one page, a worked example, the traps), `FILES` and `init` in `runner/setup.py`, `runner/templates/opencode.json` and `runner/templates/CLAUDE.md`, and the Python lines in `AGENTS.md` (items 5, 6 and 9), `Travel Companion's project.md` and `docs/agents/developer.md`.
- The guide holds what every Python project shares: uv, type hints and mypy, ruff and its 100 columns, pytest, one test file per module, and tests that use temporary repos and databases. It ends with the `[checks]` lines a Python project starts from (f121-02's and f121-03's defaults), for the setup session to copy. Softfield's own `AGENTS.md` and each project's own rules file stay as they are.
- `stacks` under `[project]`, a list of guide names, `["python"]` when missing. A name with no `docs/agents/stacks/<name>.md` raises `ConfigError`.
- The lead's jobs read the guides through `CLAUDE.md`'s imports from `~/.local/share/softfield/live/docs/`, as they read `docs/agents/owner.md`. The local developer runs with `external_directory: deny`, so first try whether opencode loads an `instructions` entry outside the repo. If it doesn't, `init` copies each guide into the project as `docs/agents/<name>.md` and lists it in `instructions`. Log which one you chose under "Built" in the card's doc.
- `docs/bootstrap.md`'s setup steps name the guides: a project in a language with no guide gets one written in its setup session, the first ticket of that kind done by the lead.

### Done when
- a project with no `stacks` key reads the Python guide; one with `stacks = ["javascript"]` and no such guide fails `doctor` with a line naming the missing guide
- a project set up with `softfield init` has its developers and its lead jobs reading `docs/agents/stacks/python.md`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
