---
id: f296-01-code-lines-kept-per-ticket
milestone: f296-show-each-milestone-s-net-code
difficulty: 3
depends_on: []
agent: lead
files:
  - runner/metrics.py
  - runner/session.py
  - runner/backfill.py
  - runner/report.py
  - .softfield/adr/52-a-review-leaves-the-code-simpler.md
  - tests/runner/test_metrics.py
  - tests/runner/test_session.py
  - tests/runner/test_report.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_session.py
  - tests/runner/test_report.py
---

### Goal
The metrics database keeps each merged ticket's code lines added and removed, so the dashboard can show a milestone's net code lines without git, and `softfield report` reads them instead of running git per ticket.

### Context
Read `.softfield/cards/f296-show-each-milestone-s-net-code.md` (D1, D2) and `.softfield/adr/52-a-review-leaves-the-code-simpler.md` (item 4). Write the tests first.
- `Git.commit_code_lines` in `runner/gitops.py` already counts one commit's code lines (no `tests/`, `docs/`, `.softfield/`, `*.md`).
- Schema steps are the `_V<n>` strings in `runner/metrics.py`; follow `_V17` for the next one, and `upsert_ticket` for the new fields.
- `record_ticket` in `runner/session.py` writes `lines_changed` from `commit_size` when it is given a commit; `sync_tickets` calls it for every ticket file at a run's start without a commit. `runner/backfill.py` writes `lines_changed` beside it too.
- `_code_lines` and `milestone_report` in `runner/report.py` take a `git` only for these counts; `write_milestone_report` passes it.
- In ADR 52 item 4, after "Computed from git each time, nothing stored.", add: "Since F296 each ticket's counts are kept in its row when it merges, and the report reads them."

### Done when
- `tickets` has `code_added` and `code_removed`; a merge recorded by `record_ticket` with a commit fills them from `commit_code_lines`
- at a run's start, a ticket row with a commit and `code_added` NULL gets both filled once; a row already filled runs no git
- `runner/backfill.py` fills them beside `lines_changed`
- `milestone_report` takes no `git`; for the same tickets its "Code lines" row and Trends' "Net code lines" are what they were (the existing test, fed through the columns)
- a ticket with no commit, or a commit git doesn't have, counts nothing and raises nothing
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
