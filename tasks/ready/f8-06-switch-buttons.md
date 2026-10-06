---
id: f8-06-switch-buttons
milestone: f8-one-queue
depends_on: [f8-05-replan, f3-25-allowance-dials, f9-17-fix-dial-colours-and-reset]
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
- The switch's state comes from the runner's state (`reserve` in `var/runs/state.json`, as f8-04 stores it); its label says what it does: "Let the factory use the week's reserve", "Let the factory use your 25% of the 5-hour window".
- Each posts a `reserve` request with subject `week` or `five_hour` and value `on` or `off`. A switch that is on says until when ("on until Mon 21:40"): it turns itself off after 24 hours.
- **The panel refreshes with the live partial** (from f4-12, folded in): move the `allowance` section of `factory_dashboard/templates/overview.html` into `/live` and its data into `_live_context`, keeping the section id `allowance` and each row's id. It stays **below Now** (owner, 2026-10-03: what's running comes first), not at the top.
- **The reserve marks read in both themes** (from f4-16, folded in): `.meter > .mark` is a 2 px line in `--warn-ink`, invisible once the fill passes it, and `.meter`'s `overflow: hidden` cuts its overhang. Draw it in `--ink` with a 1 px `--surface` outline, let it overhang (clip the fill, not the meter), and give it a `title` with its label.

### Done when
- each meter row has its switch, showing the stored state, and its request carries the right subject and value (asserted within that row)
- a meter of another agent has no switch
- `/live` returns the allowance panel, after `#running`; a mark has a `title` equal to its label
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
