---
id: f41-02-fold-the-text
milestone: f41-i-find-that-on-conversations-there
difficulty: 2
depends_on: []
files:
- factory_dashboard/templates/thread.html
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
---

### Goal
On a thread, a lead message with points shows its free text in a closed "Full reply" fold above the points.

### Context
Read the lead message branch of `factory_dashboard/templates/thread.html` (`msg.text`, then `msg.points`).
- Worked example: the `<details id="remove-seed">` fold in the same template; give the summary the same style and a 44px tap height.
- A lead message without points shows its text open, as today: its `json` block was missing or broken and the text ends with a note saying why, which must stay visible.
- Owner messages are unchanged.
- Thread tests: `test_a_fixture_reply_with_7_points_shows_each_point` and `test_on_a_phone_one_point_shows_at_a_time` in `tests/factory_dashboard/test_planning.py`; reuse their helpers.
- The factory dashboard is English only: no translation needed.

### Done when
- a lead message with points renders its text inside a `<details>` that is closed on load, summary "Full reply", placed before the points
- opening it shows the text with its line breaks, as today
- a lead message with no points renders its text open, with no fold
- an owner message renders as today
- the points, their comment fields and the phone deck are unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: built by the lead in a terminal session (owner, 2026-10-08)
```
