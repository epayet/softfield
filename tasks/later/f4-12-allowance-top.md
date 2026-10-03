---
id: f4-12-allowance-top
milestone: f4-always-on
depends_on: [f4-10-queue-live, f4-30-queue-live-tests]
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The allowance panel sits at the top of the Overview and refreshes every 5 s, so the owner sees every agent's windows without reloading or scrolling.

### Context
Read `factory_dashboard/overview.py` (`agent_allowances`, `_live_context`, `overview`), the `allowance` section of `factory_dashboard/templates/overview.html`, `factory_dashboard/templates/_partials/live.html` and the allowance tests in `tests/factory_dashboard/test_overview.py` (`allowance_client`).
- Facts: the allowance is rendered once at page load, beside Last verdict, below the Queue. Its readings only change when a job finishes, but the owner wants them current without reloading.
- Move the `allowance` section into the `/live` partial, first, above Needs you, and its data into `_live_context`. It reads only the metrics database (no agent is called). Keep the section id `allowance` and each row's id (`allow-<label>-<window>`).
- Last verdict stays where it was, on its own.

### Done when
- `/live` returns the allowance panel with the same rows as `/`
- on `/`, `#allowance` comes before `#running`
- a new reading written between two `/live` calls shows in the second
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
