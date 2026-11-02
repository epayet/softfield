---
id: f8-06-switch-buttons
milestone: f8-one-queue
depends_on: [f8-05-replan, f8-10-reserve-request-kind, f3-25-allowance-dials, f9-17-phone-allowance-bars]
difficulty: 4
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Beside Claude's week and 5-hour meters, a switch says whether the factory may use the reserve kept there, and turning it posts the owner's request.

### Context
Read D4 in `docs/milestones/f8-one-queue.md`, `factory_dashboard/requests.py` and its worked example in `docs/agents/developer.md` ("a button that asks the runner"), the allowance section of `factory_dashboard/templates/_partials/live.html`, and `tests/factory_dashboard/test_overview.py`.
- **The switch's state** is `switches` in the runner's `var/runs/state.json` (`State` in `runner/state.py`): `week` or `five_hour` -> the ISO time it was turned on; absent is off. Find the file as `_config` in `factory_dashboard/line.py` finds the config (the file is in its `runs_dir`), read it with `load_state`, and ask `switch_on` in `runner/loop.py` (on lasts `USE_RESERVE_HOURS`). No config or no file: both off.
- Its label is `SWITCHES` in `runner/loop.py`: "Let the factory use the week's reserve", "Let the factory use your 25% of the 5-hour window".
- Each posts a `reserve` request (`RESERVE` in `runner/requests.py`) with subject `week` or `five_hour` and value `on` or `off`. A switch that is on says until when ("on until Mon 21:40", as `set_switch` words it): it turns itself off after 24 hours.
- **The panel refreshes with the live partial** (from f4-12, folded in): move the `allowance` section of `factory_dashboard/templates/overview.html` into `/live` and its data into `_live_context`, keeping the section id `allowance` and each row's id. It stays **below Now** (owner, 2026-10-03: what's running comes first), not at the top.
- **The reserve marks read in both themes** (from f4-16, folded in): `.meter > .mark` is a 2 px line in `--warn-ink`, invisible once the fill passes it, and `.meter`'s `overflow: hidden` cuts its overhang. Draw it in `--ink` with a 1 px `--surface` outline, let it overhang (clip the fill, not the meter), and give it a `title` with its label.

### Done when
- each meter row has its switch, showing the stored state, and its request carries the right subject and value (asserted within that row)
- a meter of another agent has no switch
- `/live` returns the allowance panel, after `#running`; a mark has a `title` equal to its label
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 7349364
logs: var/runs/20261008-230441/f8-06-switch-buttons
```
