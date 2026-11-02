---
id: f139-02-runner-moves-projects
milestone: f139-the-factory-folder-should-actually-be
agent: lead
difficulty: 6
depends_on: [f139-01-move-home]
files:
  - runner/loop.py
  - runner/cli.py
  - docs/how-it-works.md
tests:
  - tests/runner/test_loop.py
---

### Goal
The runner moves every project to `.softfield/` on its own: Softfield first, then a restart on the moved code, then each other project the first time it opens it.

### Context
Read D5 in `.softfield/cards/f139-the-factory-folder-should-actually-be.md`, then `move_home` in runner/home.py (f139-01's), and in `runner/loop.py`: `run_projects` (the project loop, before `open_session`), `softfield_repo`, `update_live` and `RESTART_NOTE` (how a runner/ change restarts the runner today), and where `runner/cli.py` reads each project's config (`configs()`) and restarts.
- The trap: `configs()` reads each project's project.toml through `config.PROJECT_TOML`. Once the code says `.softfield`, an unmoved project reads as having none (wrong name, wrong checks): move it before its config is read, not after.
- Today's projects (2026-10-27): softfield, coucou, travel-companion live; four `test-factory-hello*` forgotten. A forgotten project is not opened, so it moves when it comes back.
- `docs/how-it-works.md` gets two lines: where a project's own folder is, and that an old `.softfield/` one is moved by the runner at its first open (F139).

### Done when
- with Softfield's code still spelling `.softfield` (a test patches `config.PROJECT_TOML`), the runner moves only Softfield's repo and returns restart before opening any project; nothing else moves
- with the code spelling `.softfield`, a project with a `.softfield/` folder is moved before its config is read and opened, and one already moved is opened as today with no move attempted
- a move that `move_home` refuses or undoes leaves that project unopened this round (said once on the console, as a project that can't open a session is), and the others run
- `softfield run --dry-run` says which projects still wait for their move
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
