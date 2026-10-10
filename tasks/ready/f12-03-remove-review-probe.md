---
id: f12-03-remove-review-probe
milestone: f12-turn-on-notifications-little-feedback-button
depends_on: []
agent: lead
priority: 100
difficulty: 1
finding: f12-turn-on-notifications-little-feedback-button-F8
tests_only: true
files:
  - tests/factory_dashboard/test_probe_tmp.py
tests:
  - tests/factory_dashboard/test_app.py
commands: [rm tests/factory_dashboard/test_probe_tmp.py]
---

### Goal
The scratch file the F12 review left in the tests is gone, so the `layout` gate passes on main again.

### Context
`tests/factory_dashboard/test_probe_tmp.py` holds no test: the review's round 1 wrote it to see what Chrome answers on a plain-http address, and a headless review can't delete a file. The `layout` gate (`layout_problems` in `runner/gates.py`) fails on it, because no module of the dashboard matches its name, and so does every developer ticket until it goes.
- Run `rm tests/factory_dashboard/test_probe_tmp.py`. Change nothing else.
- What the probe found is already tested: `test_notification_bar_shows_steps_on_insecure_origin` in `tests/factory_dashboard/test_app.py`.

### Done when
- `tests/factory_dashboard/test_probe_tmp.py` no longer exists
- `uv run runner check-all --task f12-03-remove-review-probe` passes
