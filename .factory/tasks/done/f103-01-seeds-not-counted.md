---
id: f103-01-seeds-not-counted
milestone: f103-the-number-of-things-in-planning
difficulty: 2
depends_on: [f26-02-group-counts]
files:
  - factory_dashboard/planning.py
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
Seeds no longer count as waiting for the owner: the number next to Planning, "Your desk · N" and the Overview's "N things wait for you" count only what the owner has to act on.

### Context
Read `.factory/cards/f103-the-number-of-things-in-planning.md` ("What happens today", D1, D2), then `waiting_for_you` and `desk` in `factory_dashboard/planning.py`.
- Every count reads `waiting_for_you`: the tab (`factory_dashboard/app.py`), the desk heading (`factory_dashboard/templates/planning.html`), the Overview's Needs you (`factory_dashboard/overview.py`), the Projects page (`factory_dashboard/projects.py`) and `desk_trail`. Change only `waiting_for_you`: leave out the items of the group whose key is `seeds`. `desk` still returns the Seeds group, which the desk still lists.
- f26-02-group-counts gives each desk group its own number and tests that the groups' numbers add up to "Your desk · N": that sum now leaves out the Seeds group, whose heading keeps its own number.
- `test_every_page_shows_the_planning_count_on_first_paint` in `tests/factory_dashboard/test_app.py` makes its count from two seeds: give it something that does wait for the owner instead (an open proposal or an answer wanted, as the planning tests seed them), so it still checks a number.
- The dashboard is English only: no translation needed.

### Done when
- with two seeds and one open proposal, the tab reads "Planning · 1", the desk heading "Your desk · 1", and the Overview says "1 thing waits for you on your desk"
- with seeds only, the tab reads "Planning" with no number, the Overview shows no desk line in Needs you, and the desk still lists the seeds under "Seeds, not asked about yet" with its group number
- `desk_trail`'s Next never leads to a seed's page, and "N waiting for you" leaves seeds out
- the desk groups' numbers other than Seeds add up to "Your desk · N"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 281184
logs: .factory/var/runs/20261029-091445/f103-01-seeds-not-counted
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
