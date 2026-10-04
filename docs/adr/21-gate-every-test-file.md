# ADR 21: Every test file on main is gated, whatever the queue holds

- **Status:** Accepted (by the owner, 2026-10-04)
- **Date:** 2026-10-04
- **Deciders:** project owner (accepts), Claude (drafts)
- **Supersedes:** [ADR 01](01-calibration-fixes.md) item 1 (`all-tests` ignores other queued tasks' skeleton tests)
- **Evidence:** the F3 review (`docs/reviews/f3.md`, finding f3-F6).

## Context
- **ADR 01 item 1** made the all-tests gate skip the `tests:` files of every other developer ticket in `ready/`, `escalated/` and `blocked/`, because skeleton-first put failing tests on main for each queued ticket. `runner check-all` skips them too (`runner/tasks.py` `queued_tests`, `runner/checks.py`).
- **Skeleton-first is gone.** Since ADR 07, developers write their own tests in their own branch, and lead tickets write theirs in their own job. Nothing puts failing tests on main ahead of a ticket any more, so the skip protects nothing.
- **What the skip costs now:** a `tests:` entry names a whole file, and the files developers add to are the shared ones. On 2026-10-04, `tasks/ready/` lists `tests/factory_dashboard/test_line.py` (f3-08) and `tests/factory_dashboard/test_overview.py` (f5-10, f5-11, f6-09). So the line's 67 tests and the Overview's 50 ran in no gate: not in the pre-commit hook, not in a developer's all-tests gate, not before a lead ticket's merge.
- **It let a regression in:** f5-14 (the factory look) merged with `test_no_phone_label_overlaps_another_or_leaves_its_station` red on main: its taller font made "ruff · mypy" and "tests · gates" overlap on the phone floor. `check-all` said OK. The review found it by running the file by hand, and fixed it.

## Decisions (draft)
1. **⚑ The all-tests gate and `runner check-all` run every test file on main.** `queued_tests` and the `--ignore` it feeds go. A ticket's own tests still go through `task-tests` and `tests-fail-on-main` as now.
2. **Pre-flight is unchanged:** a `tests:` file that doesn't exist yet is still fine (ADR 07 item 4). It isn't collected until a branch writes it.
3. **If a ticket ever needs failing tests on main ahead of its work** (a lead writing them for a developer), they go in a new file that only that ticket lists, marked `xfail(strict=True)` by the lead. ADR 01 rejected `xfail` because the developer would have to edit an existing test; with a file of its own, removing the mark is part of the ticket.

## Consequences
- A developer whose change breaks a shared test file now fails all-tests at once, as intended, instead of the break reaching main.
- A lead who leaves main red now blocks every developer ticket until fixed. That is already the rule for ruff and mypy (lead.md, "Your own work").

## Open questions
- None. Recommendation: accept; the change is about 20 lines in `runner/checks.py`, `runner/gates.py` and `runner/tasks.py`, with their tests, as a lead ticket.
