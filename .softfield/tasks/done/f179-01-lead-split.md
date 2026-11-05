---
id: f179-01-lead-split
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 4
depends_on: []
files:
  - factory_dashboard/queries.py
  - tests/factory_dashboard/test_queries.py
tests:
  - tests/factory_dashboard/test_queries.py
---

### Goal
`lead_split` tells, per agent and difficulty band, how the lead tickets went: merged, first time, step-ups, dollars, what Opus would have spent and what was saved, and the review findings.

### Context
Read `.softfield/cards/f179-how-is-sonnet-doing-as-an.md`, D1, D2 and D3: they define every number.
- Follow `def savings` in `factory_dashboard/queries.py`: a frozen dataclass for the row (`LeadRow`), plain functions over a read-only connection, data not text.
- Tables: `jobs` (`role = 'lead-ticket'`, `agent`, `attempt`, `outcome`, `note`, `cost_usd`, `started`), `tickets` (`difficulty`, `milestone_id`), `findings` (`ticket_id`, `severity`: `blocking`, `should-fix`, `nit`), `runs`/`projects` for the project, `milestones.key` for `key`.
- Dollars come from `dollars` in the same file, as `savings` reads them.

### Done when
- a project where Opus merged a difficulty-3 lead ticket for $1.60 and one for $1.80, and Sonnet merged one difficulty-3 ticket for $0.50: Sonnet's row "difficulty 4 or below" has 1 ticket, 1 first time, would-have $1.70, saved $1.20
- a Sonnet ticket whose first job is `parked`, then a passed Sonnet job, counts first time; a failed Sonnet attempt then a passed Opus job is Sonnet's, not first time, 1 step-up, with the Opus job's dollars in Sonnet's dollars
- a difficulty Opus never did takes Opus's mean over all its lead tickets; a ticket with no difficulty is in no row
- reviewed counts a ticket whose milestone has a passed `review` job; should-fix and blocking count its findings
- `key` keeps one milestone's tickets; `start` and `end` keep tickets whose first job started in them
- Opus's own rows have no would-have and no saving; a project with no lead ticket returns `[]`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 7677
gate_failures: ['ruff']
tokens: 8515186
```
