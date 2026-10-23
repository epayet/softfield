---
id: bug-37-allowance-marks-read-the-config
milestone: bugs
difficulty: 3
depends_on: []
area: factory
priority: 65
finding: f2-F5
files:
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's allowance marks sit where the machine's config puts Claude's reserves, whatever the owner sets them to.

### Context
Read `WEEK_MARK` and `FIVE_HOUR_MARK` in `factory_dashboard/overview.py` (lines 30–35 and where they are used, about line 672), and `def load_config` in `runner/config.py` (the `[claude]` table's `reserve` and `five_hour_reserve`).
- Today the marks are constants copied from those settings (0.70, 0.75), so they go wrong when the owner changes them.
- Read them from the config; with no config, or a value missing, fall back to today's numbers.

### Done when
- with `reserve = 0.6` in the config, the week row's mark is at 60%
- with `five_hour_reserve = 0.8`, the 5-hour row's mark is at 80%
- with no config, both are as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
