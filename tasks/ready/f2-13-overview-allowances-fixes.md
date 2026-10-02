---
id: f2-13-overview-allowances-fixes
milestone: f2
depends_on: [f2-06-overview-allowances]
difficulty: 3
finding: f2-cp2
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's allowance panel gives the week's and the month's reset date, lists the Ollama agents that have no reading as "no data yet", and its tests read each row's own text.

### Context
Read `tasks/done/f2-06-overview-allowances.md`, `factory_dashboard/overview.py` (`_format_reset`, `_agent_allowances`, `agent_allowances`), the `allowance` section of `factory_dashboard/templates/overview.html` and the allowance tests in `tests/factory_dashboard/test_overview.py`.
- Facts, reset times: `_format_reset` builds "resets on Oct 9 12:00" for a later day, but `_agent_allowances` throws that label away and writes `f"resets at {reset_clock}"`, so the week and the month show only a clock time ("resets at 12:00"), with no date. No test checks any reset text.
- Facts, "no data yet": the panel only queries the `claude-` and `copilot-` prefixes, so an agent seen in `jobs` with no reading never appears. The f2-06 ticket meant the Ollama agents (`ollama-*` in `workflow/runner.toml`), which report no readings. `test_an_agent_with_jobs_but_no_readings_says_no_data_yet` says so in its comments and only checks that "Claude" and "Copilot" appear. `write_fixture`'s jobs have no `ollama-*` agent; `LOCAL` (`local-…`) is the local model, which has no allowance and stays out of the panel.
- Facts, the other tests: `test_the_allowance_panel_shows_each_window` checks words like "week", "month" and "Claude" anywhere in the section, so they don't tell which row a percentage belongs to. `_agent_allowances` also has dead branches (`any_reading` can't be true when `readings.get(wkey)` is `None`; `if row is None: continue` after `_has_reading`).
- Put new fixture rows (an `ollama-*` job with no reading) in your own function in `tests/factory_dashboard/conftest.py`, as `write_allowance` is.

**The dashboard is English-only and never writes the database.**

### Done when
- with `write_allowance`'s rows, the Claude 5-hour row reads "80%" and "resets at" its clock time, the week row "20%" and its reset date, the Copilot month row "2%" and its reset date; each asserted within its own row
- an `ollama-*` agent with jobs and no reading has its own row saying "no data yet"; the local model has none
- a reading past its reset shows "reset since, no new reading" in that window's row, and no percentage there
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
