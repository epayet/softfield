---
id: f251-01-uptime-in-the-top-bar
milestone: f251-i-want-to-see-computer-uptime
difficulty: 2
depends_on: []
files:
  - factory_dashboard/machine.py
  - factory_dashboard/app.py
  - factory_dashboard/templates/_partials/bar_status.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_machine.py
  - tests/factory_dashboard/test_app.py
---

### Goal
Every page's top bar says how long the computer has been on since its last start: an "On 6 d 4 h" plate after the status on a wide screen, and a second line in the status words a phone shows when the dot is tapped.

### Context
Read `.softfield/cards/f251-i-want-to-see-computer-uptime.md` (D1–D3) and build the Proposed of `.softfield/cards/f251-mockup/uptime.html` (`.uptime`, `.words .on`).
- `factory_dashboard/machine.py` is new: `booted_at(now)` reads `/proc/uptime` on Linux, else `sysctl -n kern.boottime` on macOS, and returns None when neither works; `on_for(booted, now)` gives "42 min" under an hour, "5 h 12 min" under a day, then "6 d 4 h". Tests fake the file and the command; never read the real machine in a test.
- `factory_dashboard/app.py`: `top_bar` adds `uptime`, `{"for": on_for(...), "since": ...}` or None. "since" is printed in the machine's local time like the bar's other times (`queries` has the helper the paused time uses).
- `factory_dashboard/templates/_partials/bar_status.html`: the plate after the sign, its `title` saying since when; the `.on` line inside `.words`. Nothing at all when `uptime` is None.
- `factory_dashboard/static/dashboard.css`: next to `.factory-status`; the plate uses `--plate`, `--rule`, `--muted`, `--notch` only, never a status colour; in the phone block (max-width 639px) the plate hides and `.words .on` shows; on a wide screen `.words .on` hides.
- F132's `f132-08-picker-in-the-tabs` may have moved the project picker into the tabs; this ticket touches only the status's own partial and rules.

### Done when
- the Overview's top bar shows "On" and a time, with "since" and a date in its title
- on a phone width, the plate is hidden and the tapped words show "Computer on … · since …"
- the `/live` partial carries the same uptime, so an open page keeps it fresh
- `booted_at` returning None leaves no plate and no line, and the page still renders
- `on_for` gives "42 min", "5 h 12 min" and "6 d 4 h" for those spans
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: protected-paths)
attempts: 3
tokens: 3426827
logs: .softfield/var/runs/20261116-205926/f251-01-uptime-in-the-top-bar
```
