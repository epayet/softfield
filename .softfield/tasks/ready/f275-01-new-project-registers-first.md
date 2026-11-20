---
id: f275-01-new-project-registers-first
milestone: f275-a-project-created-by-web-interface
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/setup.py
  - runner/metrics.py
tests:
  - tests/runner/test_setup.py
  - tests/runner/test_metrics.py
---

### Goal
A project started from the Projects page goes first in the owner's order of projects, every other project moving down one place; a project added with `softfield init` still goes last.

### Context
Read D1 and D2 in `.softfield/cards/f275-a-project-created-by-web-interface.md`. Then `register` and `start_project` in `runner/setup.py`, and `projects_in_order` and `set_project_order` in `runner/metrics.py`; `_project_order` in `runner/requests.py` shows how a sent order is applied.
- Today `register` gives a fresh row (its `priority` still the default 100) the place after the last live project, capped at 99. `start_project` calls it with `paused=metrics.SETTING_UP`; `runner/cli.py` and `create` call it without.
- A forgotten row that comes back keeps its place, as today: only a fresh row is placed.
- D2: when the owner sends an order from the Projects page while a new project's request is still waiting, the order arrives without the new project's name. `set_project_order` must then put a left-out project that is "setting up" before the listed ones, not after.

### Done when
- a project registered by `start_project` is first in `projects_in_order`, and the projects that were there keep their order behind it
- a project registered without `paused` (the `softfield init` path) is still last, and a forgotten row that comes back keeps its old place
- `set_project_order` puts a live project it leaves out that is "setting up" first, in its old order among such projects; other left-out projects still go after the listed ones
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
