---
id: f136-02-init-asks-about-the-old-entry
milestone: f136-if-i-forgot-about-a-projject
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/setup.py
  - runner/cli.py
  - runner/metrics.py
  - runner/templates/project.toml
tests:
  - tests/runner/test_setup.py
  - tests/runner/test_metrics.py
---

### Goal
`softfield init` in a folder named like a project the database already holds asks what to do with the old entry, continue or keep it, instead of quietly taking it over.

### Context
Read D1, D2 and D4 in `.softfield/cards/f136-if-i-forgot-about-a-projject.md`, then `init` and `register` in `runner/setup.py`, the `init` and `forget` branches of `_machine_command` and `_forget` in `runner/cli.py` (its `input()` is the way to ask), the `init` parser in the same file, and `upsert_project`, `find_project`, `projects_in_order`, `set_project_paused`, `FORGOTTEN` and `SETTING_UP` in `runner/metrics.py`.
- Today `register` calls `upsert_project(conn, folder.name, …)`, which takes back a forgotten row (or a live one in another folder) with all its cards and threads.
- The new project's name is `name` under `[project]` in the `project.toml` that `init` writes from `runner/templates/project.toml` (`{name}`); `register` must register that name, not `folder.name`, once they can differ.
- "Start fresh" is f136-03: here, offer only continue and keep (and the flag's `fresh` says it is not built yet).
- Ask before any file is written or committed. `--previous continue|keep` answers without asking; with no terminal (`sys.stdin.isatty()` false) and no flag, stop with a message naming the choices and the flag.
- `softfield forget`'s closing line says that a later `init` under the same name will ask.

### Done when
- `init` in a new folder `hello` with a forgotten `hello` row asks; "keep" renames the old row `hello-1` (the first free `-N`), still forgotten with its milestones, and registers a new `hello`
- "continue" is offered only when the folder's `.softfield/project.toml` names the forgotten project: it writes and commits nothing, points the row at the folder and sets it setting up
- with a live `hello` in another folder, the only choice is a new project `hello-2`, written in its `project.toml` and registered under it; the live row is unchanged
- with no row of that name, `init` runs as today, without a question
- no terminal and no `--previous`: `init` exits 1 having written nothing
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
