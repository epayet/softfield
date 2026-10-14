---
id: f50-01-ripe-after-review
milestone: f50-the-data-safety-review-it-asks
depends_on: []
difficulty: 2
files:
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
A card ripens only once its review is written: every ticket done and its sign-off sheet stored.

### Context
Read `_field` in `factory_dashboard/line.py` and `_ripe` in `factory_dashboard/planning.py` (the desk's "Finished, to talk through" reads `field["ripe"]`, so it follows).
- The sheet is the `signoff` column of `milestones` (JSON, written by the review loop); NULL means no review yet. Add it to `_field`'s query.
- A milestone with every ticket done and no sheet goes to `rows`, with its counts as now (`ready` 0, `running` 0, `done` = `total`), not to `ripe`.
- Done milestones still go to the stash, sheet or not.
- The existing tests that make a ripe milestone without a sheet must store one now (`metrics.upsert_milestone(..., signoff={...})`).

### Done when
- every ticket done, `signoff` NULL, status "review due": the milestone is in `field["rows"]` with done equal to total, not in `field["ripe"]`, and not on the desk's "ripe" group
- the same with a sheet stored: in `field["ripe"]` and on the desk
- a done milestone with no sheet is in the stash
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: built by the lead in a terminal session (owner, 2026-10-08)
```
