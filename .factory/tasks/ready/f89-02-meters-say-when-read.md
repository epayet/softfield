---
id: f89-02-meters-say-when-read
milestone: f89-does-allowance-refresh-at-the-beginning
agent: developer
difficulty: 2
depends_on: [f32-01-lead-window-resets]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/_partials/allowance.html
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
The planning room's lead window and the Overview's allowance rows say when each reading was taken.

### Context
The picture to build: `.factory/cards/f89-mockup/lead-window.html` (Proposed). Read D3 in `.factory/cards/f89-does-allowance-refresh-at-the-beginning.md`, then `WindowAllowance`, `_reset_label` and `_agent_allowances` in `factory_dashboard/overview.py`, `#lead-window` in `factory_dashboard/templates/planning.html`, and `factory_dashboard/templates/_partials/allowance.html`.
- `WindowAllowance` gains `read_label: str | None`, from the reading row's `at` (`metrics.latest_readings` returns the whole row), in the local time zone as `_reset_label` shows resets: "read at 03:59" on the same day as `now`, "read on Oct 26 22:10" otherwise; None when the window has no reading. Add a `_read_label` beside `_reset_label`, in the same shape.
- In `#lead-window`, the header becomes a row: the title on the left, the 5-hour row's `read_label` on the right in the mono font (`var(--mono)`, `var(--ink-2)`). Nothing when it is None.
- In the allowance partial, each row's small line adds its `read_label` as one more `<small>`, after the reset or status.

### Done when
- with a 5-hour reading taken at 03:59 today, `#lead-window` shows "read at 03:59" once
- a reading from the day before shows "read on <Mon> <d> <HH:MM>"
- with no reading, the tile shows no "read" text
- each Claude row of `#allowance` on the Overview shows its own "read at …"
- assert within `#lead-window` and `#allowance`, on their text with tags stripped (`_text` in `tests/factory_dashboard/test_planning.py`)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
