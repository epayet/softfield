---
id: bug-06-review-suite-fits-one-call
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 26
files:
  - runner/prompts.py
  - runner/milestone.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
A headless review can see the whole test suite finish inside one Bash call.

### Context
Read the review prompt in `runner/prompts.py` (the line "fix it yourself now, keeping `uv run pytest -q {tests}` green") and where `runner/milestone.py` fills `{tests}`; `test_workers` in `runner/config.py` is how `softfield check-all` runs the suite on pytest-xdist's workers (F71). `runner/**` is protected: tests first.
- `uv run pytest -q tests/runner tests/factory_dashboard`, the command a review is told to keep green, now takes longer than a Bash call's 10-minute limit: neither of F172's two review rounds saw it finish (78% and 93%); `tests/factory_dashboard/test_planning.py` alone takes about 4 minutes.
- Give the review's command the project's workers (`-n <test_workers>` when it is above 0), so it runs as `check-all` does.

### Done when
- with `test_workers = 16`, the review prompt's command is `uv run pytest -q -n 16 <tests>`
- with `test_workers = 0`, it is as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
