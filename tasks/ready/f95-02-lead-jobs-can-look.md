---
id: f95-02-lead-jobs-can-look
milestone: f95-overview-currently-says-i-have-2
priority: 0
depends_on: []
difficulty: 10
agent: lead
files:
  - runner/look.py
  - runner/cli.py
  - runner/loop.py
  - runner/milestone.py
  - runner/planner.py
  - docs/workflow.md
tests:
  - tests/runner/test_look.py
  - tests/runner/test_loop.py
---

### Goal
Planner and review jobs can read the metrics database and any dashboard page through one read-only command, `uv run runner look` (ADR 28).

### Context
Read `docs/adr/28-lead-jobs-can-look.md` (every item), `runner/cli.py` (`main`, `_apply_requests`, `_NO_REQUESTS`), `runner/loop.py` (`run_planner`), `runner/milestone.py` (the review's `JobSpec`), `runner/claude.py` (`shell_note`), `factory_dashboard/app.py` (`create_app`) and `factory_dashboard/queries.py` (`connect`). `runner/**` is protected: write the tests first, each failing for the right reason.
- `look sql "<SELECT>"`: open with `connect`, then allow reads only through SQLite's authorizer, so a write, an `ATTACH` (it can create a file even on a read-only connection) and a changing `PRAGMA` are refused by SQLite, not by matching the text. One statement. Cap the rows (200) and the length of a cell, and say when the output was cut.
- `look page <address>`: a GET on `create_app` in process (no server, no port), for the config's database and project. Print an HTML page as text (no scripts, styles or tags, blank runs collapsed) and a JSON answer as is; cap the length and say when it cut. Only GET exists in the command. Check no GET route of the dashboard writes.
- `look` is in `_NO_REQUESTS`, and does nothing else a runner command does at its start.
- The prefix `uv run runner look` joins the commands of the planner's job and the review's job, nowhere else. The planner's prompt gets one line: the command, its two forms, and "look before answering what the owner sees".
- An error (bad SQL, no such page) prints one plain line and exits non-zero.

### Done when
- `look sql` prints a SELECT's rows with their column names; an INSERT, UPDATE, DELETE, `ATTACH`, a writing `PRAGMA` and two statements in one are each refused, and the database file is unchanged after each
- more rows than the cap print the cap and a line saying so
- `look page /planning` prints the desk's words (a group title and an item's title from the fixture) with no tag or script in the output; `look page` on the floor's data address prints JSON
- `look page` on an unknown address exits non-zero with one line
- running `look` applies no open owner request and changes nothing in the database or the repo
- the planner's job and the review's job carry the prefix; a developer's, a checkpoint's and an escalation's don't
- `docs/workflow.md` lists the command with the others
- the listed tests pass, and fail without the change
