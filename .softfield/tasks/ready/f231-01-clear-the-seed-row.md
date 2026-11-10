---
id: f231-01-clear-the-seed-row
milestone: f231-there-are-many-bugs-in-the
agent: lead
difficulty: 1
depends_on: []
commands: [rm .softfield/tasks/later/, softfield look]
files:
  - .softfield/tasks/later/bug-05-idle-restart-waits-for-a-commit.md
  - .softfield/tasks/later/f9-12-fix-the-desktop-test-does.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
The set-aside tickets the owner agreed to drop are gone from `.softfield/tasks/later/`, so the board's Seed column holds the owner's ideas and the few bugs worth a run.

### Context
Read "The triage" in `.softfield/cards/f231-there-are-many-bugs-in-the.md`. The runner marks a ticket's row `removed` once its file has left `.softfield/tasks/` (`def remove_missing_tickets` in `runner/metrics.py`), so the board drops it by itself.
- Remove, with `rm`, each file in `.softfield/tasks/later/` whose id is one of: bug-05, bug-08, bug-09, bug-10, bug-11, bug-12, bug-13, bug-14, bug-15, bug-16, bug-17, bug-18, bug-19, bug-20, bug-21, bug-22, bug-23, bug-24, bug-25, bug-26, bug-27, bug-28, bug-29, bug-30, bug-31, bug-32, bug-33, bug-34, bug-35, bug-37, bug-38, bug-39, bug-40, bug-41, bug-42, bug-43, bug-44, bug-45, bug-46, bug-47, bug-50, bug-52, bug-53, bug-55, bug-58, bug-61, bug-62, and f9-12 (the work bug-44 asked for).
- Leave every other ticket where it is: bug-36 and bug-60 stay set aside, and the seven the plan queued are in `.softfield/tasks/ready/`.
- A file already gone is fine: say so in the commit, and go on.

### Done when
- none of the 48 files listed is in `.softfield/tasks/later/`, and nothing else under `.softfield/tasks/` changed
- `softfield look page /board` lists none of those ids in the Seed column
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)
