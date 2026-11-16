---
id: f133-02-init-picks-a-series
milestone: f133-each-project-has-its-own-series
agent: lead
difficulty: 2
depends_on: [f133-01-cards-take-the-projects-series, f236-01-doctor-registers-the-project]
files:
  - runner/setup.py
  - runner/templates/project.toml
  - runner/instructions/bootstrap.md
tests:
  - tests/runner/test_setup.py
---

### Goal
`softfield init` gives a new project a series letter no other project in the factory uses, so its first card is H1 for "hello", not M1.

### Context
Read D3 in `.softfield/cards/f133-each-project-has-its-own-series.md`, then `init` and `first_card` in `runner/setup.py` (as F136 and F236 left them: `softfield create` now adds the project to the factory, not `init`), `runner/templates/project.toml`, `project_series` in `runner/planner.py` (f133-01), `projects_in_order` in `runner/metrics.py` and step 7, "The first card", in `runner/instructions/bootstrap.md`.
- The pick: the folder name's first letter, else its first two letters, else the first free letter a–z, using only the name's letters; never `f`, `m`, or a series a project in the factory uses. A project's series is `project_series` of its `repo`; a repo that is missing or unreadable counts as `m`.
- The template gets `series = "{series}"` under `[project]`, with a one-line comment saying the setup session may change it before the first card.
- `runner/instructions/bootstrap.md`: the first card is `.softfield/cards/<series>1-<slug>.md`, headed `# Milestone <SERIES>1: <title>`, the series read from the project.toml, and its header line has no `**Area:**`.
- `first_card`'s docstring example follows. The hand-over already takes the key from the card's name.

### Done when
- init on a folder `hello` with softfield (`f`) and coucou (no series) in the factory writes `series = "h"`
- init on `hello-2` with a project already using `h` writes `series = "he"`
- a folder whose first letter is `f` or `m` (`maps`) never gets `f` or `m`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
