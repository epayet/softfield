---
id: f2-08-report-fixes
milestone: f2
depends_on: []
agent: lead
difficulty: 4
files:
  - factory_dashboard/queries.py
  - factory_dashboard/agents.py
  - runner/report.py
  - runner/backfill.py
tests:
  - tests/factory_dashboard/test_queries.py
  - tests/runner/test_report.py
  - tests/runner/test_backfill.py
---

### Goal
The numbers credit Sonnet's developer work, leave removed tickets out, and keep each milestone's real status.

### Context
Read `docs/reviews/factory-f1.md` findings 5, 7 and 8, and `factory_dashboard/queries.py` (`_is_lead`, the savings functions), `runner/report.py` and `runner/backfill.py` (the milestone rows). Test-first.
- **Sonnet's lines:** `_is_lead` treats every `claude-*` agent as the lead, so f1-28, f1-31 and f1-52 (`merged_by = claude-sonnet`, 235, 148 and 281 lines) count 0 lines and their Sonnet jobs as support: `runner report f1` shows "claude-sonnet | 3 | 0 | … | −$1.33". The lead is the role, not the harness: a job is the lead's when its role is one of the lead's (`lead-ticket`, `direction`, `escalation`, `checkpoint`, `review`, `narrative`), and a developer ticket merged by any developer agent counts its lines, with that agent's own jobs as its cost. `factory_dashboard/agents.py` has its own `_is_lead`: same fix.
- **Removed tickets:** "Tickets merged 48 of 59" counts the `removed` rows (f1-30-allowance-forecast and the six moved to F3). Leave them out of the total.
- **Backfill's status:** it writes `"done" if ended else None`, so M4's "in review" is lost and M0 has none. Read the status from the milestone doc's `> **Status: …**` line.

### Done when
- a developer ticket merged by `claude-sonnet` has its lines and a positive "doing it itself" in the savings, with its Sonnet jobs as its cost
- removed tickets are out of "Tickets merged N of M"
- after backfill, M4's status is "in review" and M0's "done"
- `uv run runner check-all --task f2-08-report-fixes` passes
