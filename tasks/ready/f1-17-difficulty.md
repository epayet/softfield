---
id: f1-17-difficulty
milestone: f1
depends_on: [f1-16-developer-rename]
agent: lead
difficulty: 4
files:
  - runner/tasks.py
  - runner/backfill.py
  - docs/task-writing.md
  - docs/task-format.md
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_backfill.py
---

### Goal
Tickets carry `difficulty:` from 1 to 10, set by a short rubric, and M1–M4's tickets get theirs.

### Context
Read `docs/adr/14-developers-and-agents.md` item 5, and `docs/milestones/f1.md`'s ticket table (every f1 ticket already has one, set by the lead from the same thinking).
- **Parse:** `difficulty` is an optional integer from 1 to 10 on `Task`; anything else is a `TaskError`. `difficulty_corrected:`, set by the lead at review when the first estimate was off, is parsed the same way. The runner's writes (f1-03) store both.
- **The rubric** in `docs/task-writing.md`: a short table from the factors (concepts, files to read and to change, dependencies, a new pattern, UI, i18n, offline), anchored on real tickets: m1-03 (a list count) low, m4-06 (wiring four components with i18n and offline) high, 10 = "only the lead should do this". Mention the field in `docs/task-format.md`.
- **M1–M4:** add `difficulty:` to each ticket in `tasks/done/m*.md` (frontmatter only; the footers stay), judged from the ticket and its result; `runner/backfill.py` reads it into `tickets.difficulty`.

### Done when
- `difficulty: 11`, `0` and `"hard"` are refused; a missing one is `None`
- every `tasks/done/m*.md` has a difficulty, and the backfill stores it
- `uv run runner check-all --task f1-17-difficulty` passes
