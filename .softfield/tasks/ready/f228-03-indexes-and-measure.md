---
id: f228-03-indexes-and-measure
milestone: f228-loading-the-overview-page-is-slow
agent: lead
difficulty: 2
depends_on: [f228-01-trends-reads-once, f228-02-one-floor-per-request]
commands: [softfield look, rm .softfield/tasks/later/bug-36-live-builds-the-board-once.md]
files:
  - runner/metrics.py
  - tests/runner/test_metrics.py
  - .softfield/cards/f228-loading-the-overview-page-is-slow.md
tests:
  - tests/runner/test_metrics.py
---

### Goal
The per-milestone reads use indexes, and the card records how fast the pages are now, measured the way they were measured before.

### Context
Read `.softfield/cards/f228-loading-the-overview-page-is-slow.md` ("What happens today", D5).
- `runner/metrics.py`: append the next step to `MIGRATIONS`, creating indexes on `jobs (ticket_id)`, `jobs (milestone_id)` and `tickets (milestone_id)`. Follow `_V14` for its shape and comment.
- `tests/runner/test_metrics.py` asserts the number of migrations: update it.
- Measure on the live database with `softfield look page`, the addresses in the card's table: `/?project=coucou`, `/runs?project=softfield`, `/board?project=softfield`, `/away?project=softfield`, `/live?project=softfield`, `/?project=softfield`, `/milestones?project=softfield`. Put `softfield look sql "SELECT strftime('%H:%M:%f','now')"` before and after each, as separate commands. Each interval then holds one page and one such query, as the card's figures do.
- Write the figures in a `## Measured after` section of the card, beside the ones before. If softfield's Overview still takes more than 2 s, say what takes the time and propose a fix: don't widen this ticket.
- Remove `.softfield/tasks/later/bug-36-live-builds-the-board-once.md`: f228-02 did its work.

### Done when
- a database at the previous version migrates and has the three indexes, and its rows are unchanged
- the card has its `## Measured after` section, with all seven figures
- `.softfield/tasks/later/bug-36-live-builds-the-board-once.md` is gone
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
