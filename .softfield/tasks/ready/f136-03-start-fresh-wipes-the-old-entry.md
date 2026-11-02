---
id: f136-03-start-fresh-wipes-the-old-entry
milestone: f136-if-i-forgot-about-a-projject
agent: lead
difficulty: 3
depends_on: [f136-02-init-asks-about-the-old-entry]
files:
  - runner/metrics.py
  - runner/setup.py
  - runner/cli.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_setup.py
---

### Goal
`softfield init`'s third choice, "start fresh", deletes the forgotten project's old entry and everything under it, once the owner types its name, and the new project starts with nothing behind it.

### Context
Read D2 and D3 in `.softfield/cards/f136-if-i-forgot-about-a-projject.md`, then the question f136-02 added to `init` (`runner/setup.py`, `runner/cli.py`) and the schema at the top of `runner/metrics.py` (`_V1` to the last `_V…`), for every table with a `project_id` and those under them.
- Deleting is the owner's choice (2026-10-27, F136). Add `metrics.delete_project(conn, project_id)`: one transaction, the children before their parents (`planner_messages`, `findings`, `jobs`, then `planner_threads`, `work_queue`, `owner_requests`, `owner_items`, `tickets`, `runs`, `milestones`, then the `projects` row). `rating_changes` rows stay, with `ticket_id` set to NULL; `usage_events` stays.
- Offered only for a forgotten row, never a live one. The prompt says what goes (cards, tickets, threads, runs and their costs) and asks for the project's name typed back; anything else cancels with nothing written. `--previous fresh` needs `--yes` too.

### Done when
- "start fresh" on a forgotten `hello` with cards, tickets, a thread with messages, a run with jobs and a rating change leaves no row under its old id, the rating change with `ticket_id` NULL, and a new `hello` registered setting up
- a wrong name typed back cancels: the database and the folder are unchanged
- `--previous fresh` without `--yes` exits 1 having written nothing
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
