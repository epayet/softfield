---
id: f262-01-archive-a-project
milestone: f262-i-want-ability-to-archive-a
difficulty: 3
depends_on: [f124-01-a-project-pauses-alone]
files:
  - runner/metrics.py
  - runner/requests.py
  - runner/loop.py
  - runner/cli.py
  - factory_dashboard/requests.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
agent: lead
---

### Goal
The owner can archive a project, and unarchive it, with a request: an archived project is held as F124's pause holds one, its session and planning still go, and the runner says it is archived.

### Context
Read `.softfield/cards/f262-i-want-ability-to-archive-a.md` ("What happens today", D1 to D3 and D6), then D1 to D4 of `.softfield/cards/f124-pause-one-project-from-the-projects.md`, which f124-01 built.
- `projects.paused`, `set_project_paused`, `SETTING_UP`, `FORGOTTEN` and f124-01's `paused_by_you` are in `runner/metrics.py`; `ARCHIVED` and `is_archived(row)` go beside them.
- f124-01's `pause_project` / `resume_project` in `_apply` (`runner/requests.py`) are the example for the two new kinds; add them to `KINDS` in `factory_dashboard/requests.py`.
- The hold f124-01 gives a paused project (in `runner/loop.py`, and which projects keep a session in `_project_configs`, `runner/cli.py`) applies to an archived one too.
- `_print_plan` in `runner/loop.py` gives each ticket its wait; `_guide` in `runner/cli.py` prints each project's `paused`.

### Done when
- an `archive_project` request on a running or paused project sets its `paused` to "archived" and answers "archived: off the picker, its tickets wait"; again, "already archived"; on a project being set up, "being set up: `softfield doctor` hands it over", its `paused` unchanged
- `unarchive_project` sets `paused` to NULL and answers "unarchived: back in the list, last"; on a project not archived, "not archived"
- with softfield archived and coucou running, a round runs coucou's ticket, never softfield's; softfield's queued planner job still runs and its requests are applied (an unarchive among them)
- while archived, its activity is `Idle: archived`; `--dry-run` says its tickets are "archived"; a bare `softfield` lists it "(archived)"
- `projects_in_order` still returns an archived project; `is_archived` is true for "archived" only
- the dashboard's `POST /requests` takes both kinds
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
