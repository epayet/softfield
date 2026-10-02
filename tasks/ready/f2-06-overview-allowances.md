---
id: f2-06-overview-allowances
milestone: f2
depends_on: []
difficulty: 4
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview shows every agent's allowance: each window's latest reading and when it resets.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`. `write_fixture`'s numbers are pinned by `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py`: put your rows in a function of your own in `tests/factory_dashboard/conftest.py`, as `write_live` is.
- Today the panel is Claude's only (`claude_allowance`, "Claude allowance, last 5 h"), estimated from job tokens. Replace it with one row per window, from `usage_events` rows of kind `reading` (columns `agent`, `window`, `value` from 0 to 1, `resets_at`, `at`): the latest reading per window.
- Claude's readings come from both `claude-opus` and `claude-sonnet` but are one account: show them once, as "Claude", with its `five_hour` ("5-hour window") and `seven_day` ("week") windows. Copilot (`copilot-auto`) has a `month` window.
- Mark the week at 70% ("reserve kept for the lead from here") and the 5-hour window at 75% ("kept for you from here"). Write these two numbers as constants at the top of `factory_dashboard/overview.py`, each with a comment naming `workflow/runner.toml`'s `[claude]`.
- A reading whose reset has passed shows "reset since, no new reading". Agents seen in `jobs` with no reading (the Ollama ones) say "no data yet".
- Every bar says what it means in words (lead.md: no unexplained marks).

Facts from the first run (escalated, restarted from main):
- `runner.metrics.latest_readings(conn, agent_prefix)` (`runner/metrics.py`) already returns each window's latest reading, keyed by window, for every agent whose name starts with `agent_prefix`; `queries.LEAD_PREFIX` is `"claude-"`.
- The `overview` route receives `now: Now`; tests pin it to `NOW` through `get_now`. Compare `resets_at` with that `now`, never `datetime.now()`.
- `_clock` in `overview.py` formats a time as `%H:%M`; a week's or a month's reset also needs its date.
- Only the allowance part of `overview.py` changes: `Allowance`, `_claude_equivalents`, `claude_allowance` and `WINDOW` are used nowhere else. `_age`, `_drain` and the route's other context keys stay as they are.
- `test_overview.py` imports `claude_allowance` (line 6), and `test_the_allowance_bar_counts_this_windows_claude_tokens` and `test_without_a_refusal_the_allowance_has_no_limit` pin the old panel. That file is in your `tests:`: replace those two tests with tests of the new panel.
- For a client over your rows, copy `milestone_detail_with_scores_client` in `conftest.py`.
- The first run's edits duplicated the route's `render(...)` block and the file stopped parsing. Replace a whole function in one Edit, and run `uv run ruff check factory_dashboard` after each edit.

**The dashboard is English-only and never writes the database.** Tests check the panel's text, not only that the page answers 200.

### Done when
- with readings of 0.8 (5-hour) and 0.2 (week) for Claude and 0.02 for Copilot's month, the panel shows "80%", "20%" and "2%" with their reset times
- an agent with jobs but no readings shows "no data yet"
- a reading past its reset shows "reset since"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 184779
logs: var/runs/20261002-115807/f2-06-overview-allowances
```
