---
id: f9-28-allowance-live
milestone: f9-line-polish
depends_on: [f9-16-no-ollama-allowance]
difficulty: 3
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/overview.py
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
The Overview's allowance panel keeps itself up to date like the queue does, with "How to read the allowance" at its bottom, and the planning room's lead window shows Claude's week under its 5-hour window.

### Context
Read the `#allowance` section in `factory_dashboard/templates/overview.html`, and how `#live-queue` above it refreshes: a `div` with `hx-get="/live{{ q }}"`, `hx-trigger="every 5s [window.liveIdle()]"` and `hx-select="#queue"`, whose section `factory_dashboard/templates/_partials/live.html` includes. Follow it: move the panel into a partial `factory_dashboard/templates/_partials/allowance.html`, include it from both, and wrap it in a `#live-allowance` div the same way. Read `planning` in `factory_dashboard/planning.py` (it picks only Claude's `five_hour` from `agent_allowances`) and `#lead-window` in `factory_dashboard/templates/planning.html`.
- The owner (2026-10-07): "whenever claude starts or finishes something, i expect to see the allowance updated"; "move how to read allowance at the bottom of the box, rather than top"; "the planning lead's window just shows the 5 hour window, i also want the week allowance".
- Claude's readings already reach the database during a job (`usage_events`, kind `reading`); only the page doesn't refresh.
- The lead window's week row: the same bar as the 5-hour row, its mark at the week's own `mark` (`WEEK_MARK`, "reserve kept for the lead from here"), and the words "week {{ percent }}".
- The live context must give `allowance` (`agent_allowances`) to `factory_dashboard/templates/_partials/live.html`; `_live_context` in `factory_dashboard/overview.py` builds it.

### Done when
- `/live` holds `#allowance` with a reading added after page load (a test inserts a newer `reading` and finds its percent in `/live`)
- on `/`, the "How to read the allowance" details come after the last allowance row inside `#allowance`
- `/planning`'s `#lead-window` shows a 5-hour row and a week row, each with its own percent
- assert within `#allowance` and `#lead-window`, on their text with tags stripped and entities unescaped (`_text` in `tests/factory_dashboard/test_planning.py`)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 4257
gate_failures: ['stopped', 'stopped']
tokens: 2315947
```
