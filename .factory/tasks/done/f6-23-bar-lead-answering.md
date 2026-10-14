---
id: f6-23-bar-lead-answering
milestone: f6-planning-room
depends_on: []
difficulty: 2
files:
  - factory_dashboard/app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
While the factory is paused and the lead answers the owner (a planner job runs during the pause), the top bar says so, instead of only "Paused by you since HH:MM" as if nothing moved.

### Context
Read `factory_status` in `factory_dashboard/app.py` and `running_jobs` in `factory_dashboard/overview.py`. Follow the status table in `tests/factory_dashboard/test_app.py`: `test_the_top_bar_says_what_the_factory_does_with_pause_or_resume`, its setups (`_pause_held_client`) and its `ids`.
- Since f6-14, a pause holds every ticket and support job, but the lead's planner jobs still run, so the owner can talk a change through on `/planning` while the line holds. A planner job is a `jobs` row with `role` `planner`.
- The owner (2026-10-07): "it would be good to see in a very obvious way from the top bar whether the factory is running, idle (nothing to do) or paused".
- While paused (`queries.paused_since`) and a live job's `role` is `planner`, the words are "Paused by you since HH:MM · the lead is answering you", with the same tone and the Resume button as the plain pause. A pause with no live planner job keeps today's words.

### Done when
- paused with a live planner job: the bar reads "Paused by you since 11:40 · the lead is answering you" with Resume, on `/`, `/planning`, `/tickets` and `/live`
- paused with a live job that is not a planner (an old row from before the pause): the bar reads "Paused by you since 11:40" alone
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1510
gate_failures: []
tokens: 1146145
```
