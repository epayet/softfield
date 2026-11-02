---
id: f121-01-main-branch-per-project
milestone: f121-projects-not-on-main-or-not
agent: lead
difficulty: 5
depends_on: []
files:
  - runner/config.py
  - runner/loop.py
  - runner/planner.py
  - runner/requests.py
  - runner/milestone.py
  - runner/bench.py
  - runner/setup.py
  - runner/prompts.py
  - runner/templates/project.toml
tests:
  - tests/runner/test_config.py
  - tests/runner/test_setup.py
  - tests/runner/test_loop.py
---

### Goal
Each project names its main branch in `.softfield/project.toml`, and the runner, the planner and `softfield init` use it instead of assuming `main`.

### Context
Read D1 in `.softfield/cards/f121-projects-not-on-main-or-not.md`, then `project_checks` in `runner/config.py` (the pattern for reading `project.toml`), `MAIN` in `runner/loop.py`, `_MAIN` in `runner/planner.py`, and `init` and `doctor` in `runner/setup.py`.
- The key is `main` under `[project]`; missing or unreadable, it is `"main"`. Add a `project_main` function, taking the repo, to `runner/config.py`.
- `MAIN` is a module constant today, used about 80 times across loop, planner, requests, milestone and bench. The runner works on several projects, so the main branch is read once per project session and carried by it; no module constant is left. `prompts.py` writes `git diff main...task/{id}`: it takes the project's.
- `init` refuses a repo on another branch today; it writes `main = "<branch>"` into the new `project.toml` instead. A folder with no repo, or no commit yet, still gets `main`.
- `doctor`'s "everything committed, on main" names the project's branch.
- Add a commented `main = "main"` line to `runner/templates/project.toml`. Softfield's own `.softfield/project.toml` gets no key: the default is right.

### Done when
- a project whose `project.toml` says `main = "master"` has its tickets branched from, merged into and diffed against `master`, and its planner drafts checked out from it
- a project with no `main` key behaves exactly as today
- `softfield init` on an existing repo on `master` sets it up and writes `main = "master"`; on a dirty repo it still refuses
- `doctor` passes on a clean `master` checkout of such a project, and says "on master"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
