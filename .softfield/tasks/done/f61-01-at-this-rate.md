---
id: f61-01-at-this-rate
milestone: f61-on-claude-usage-page-there-is
depends_on: [f9-29-week-pace]
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Under each of Claude's two meters, a line says when the window runs out at this rate, and a hatched ghost on the meter shows where it will be at the reset.

### Context
Read D1 to D6 in `.softfield/cards/f61-on-claude-usage-page-there-is.md`: the wording, the rate, when to say nothing, and where the code goes.
- The picture to build: `.softfield/cards/f61-mockup/at-this-rate.html` (Proposed).
- Follow `_reset_label` and `_agent_allowances` in `factory_dashboard/overview.py`; the meter and its legend are in `factory_dashboard/templates/_partials/allowance.html`. The `--ghost` token is at the top of `factory_dashboard/static/dashboard.css`.
- The reading's own time is the row's `at` in `usage_events` (`latest_readings` in `runner/metrics.py`).
- Worked example from the database: the week read 58% on 2026-10-21 at 22:44 (+01:00), resetting 2026-10-26 17:00. The window started 2026-10-19 17:00, so it is out at about 13:38 on 2026-10-23, 3 days 3 h before the reset.

### Done when
- `forecast` is pure and tested on: the worked example above; a window that lasts (with its projected use at the reset); a reading before 10% of the window has passed (no line); a reading of 0; an out time already past ("any time now")
- the Overview's Claude week and 5-hour rows show the line and the ghost, as in the mock-up; Copilot's row and a stale or missing reading show neither
- the legend has the ghost's line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 6889
gate_failures: ['stopped', 'stopped']
tokens: 7754280
```
