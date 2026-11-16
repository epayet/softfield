---
id: f133-01-cards-take-the-projects-series
milestone: f133-each-project-has-its-own-series
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/planner.py
  - runner/requests.py
  - .softfield/project.toml
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
---

### Goal
A new card's key takes its project's own series letter from `.softfield/project.toml`, not its area, so a new project's first card is not one more M1.

### Context
Read D1 and D2 in `.softfield/cards/f133-each-project-has-its-own-series.md`, then `SERIES`, `next_key`, `project_area`, `_area`, `planting` and `seed_area` in `runner/planner.py`, and `_plant` in `runner/requests.py`. F171's ticket f171-04 added `project_area`, read from `area` under `[project]`.
- `project_series(repo)` replaces `project_area`: `series` under `[project]`, one to three lowercase letters and not `bug`; anything else, or no file, is `m`.
- Softfield's `.softfield/project.toml`: replace `area = "factory"` and its comment with `series = "f"` and a one-line comment (D1).
- `next_key(repo, taken)` drops its area argument; every caller follows. `SERIES` goes. A plant's `area` is no longer used for the key, and never refused.
- Keys already given are not renamed.

### Done when
- a card planted in a project whose project.toml says `series = "h"` is `h1`, then `h2`; `f` and `m` keys already in its repo don't count
- a project with no `series`, or one not valid (`"bug"`, `"H1"`, `"abcd"`), gets `m` keys
- a plant carrying `"area": "factory"` in an `m` project gets an `m` key
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
