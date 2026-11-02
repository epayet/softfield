---
id: f121-05-a-project-on-master-not-python
milestone: f121-projects-not-on-main-or-not
agent: lead
difficulty: 4
depends_on: [f121-01-main-branch-per-project, f121-03-what-counts-as-a-test, f121-04-jobs-run-the-projects-checks]
files:
  - runner/setup.py
  - runner/templates/project.toml
  - tests/runner/test_setup.py
  - tests/runner/test_gates.py
tests:
  - tests/runner/test_setup.py
  - tests/runner/test_gates.py
---

### Goal
The proof: a project on `master` whose checks are not Python is set up with `softfield init`, passes `softfield doctor`, and its gates pass good work and stop bad work.

### Context
Read the Plan in `.softfield/cards/f121-projects-not-on-main-or-not.md` (its Done when and D1–D6), then `init` and `doctor` in `runner/setup.py`, and `run_gates` and `GATES` in `runner/gates.py`.
- The test project is built in a temporary folder, on `master`, with no Python: its `[checks]` are plain shell commands (`sh -c …`) for `lint`, `fix` and `test`, `test_files = ["src/**/*.test.sh"]`, `fails_on_main = [1]`, `mypy = []`, no layouts. No Node is needed on the machine.
- Check every D1–D6 default and key against what f121-01 to f121-04 built; fix what disagrees in the card's Decisions and log it under "Built" in the card's doc.
- If `init` or `doctor` still assumes Python anywhere (a `uv` call, a `tests/` folder, `pyproject.toml`), make it read the project's keys.

### Done when
- `softfield init` on that project writes `main = "master"`, and `softfield doctor` passes once its `project.toml` holds the shell checks
- a branch adding code and a `src/x.test.sh` that fails without it passes every gate
- the same branch with a lint command that fails is stopped by `lint`; with a test that passes on main's code, by `tests-fail-on-main`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
