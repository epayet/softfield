---
id: f9-13-home-without-clog-and-verdict
milestone: f9-line-polish
depends_on: [f3-32-remove-test-spacer]
difficulty: 2
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview no longer shows the "What clogged the line today" and "Last verdict" panels.

### Context
Read `factory_dashboard/templates/overview.html` (the `#clog` and `#verdict` sections), the route in `factory_dashboard/overview.py` (`clog_biggest`, `last_verdict`), and their tests in `tests/factory_dashboard/test_overview.py` (the section ids list near the top, the clog and verdict tests).
- The owner (2026-10-06): neither panel helps on the home page. The verdict stays on each milestone's page.
- Keep `line.clog` itself: the floor and f9-01 use it. Remove only what feeds the two panels, and their tests.

### Done when
- `/` has no `#clog` and no `#verdict` section; every other section is still there, in order
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2059
gate_failures: []
tokens: 1175078
```
