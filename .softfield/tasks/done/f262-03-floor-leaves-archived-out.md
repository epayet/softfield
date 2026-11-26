---
id: f262-03-floor-leaves-archived-out
milestone: f262-i-want-ability-to-archive-a
difficulty: 1
depends_on: [f262-02-archive-on-the-projects-page, f132-05-floor-every-project]
files:
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's live view and the floor of every project, which F132 built, draw no archived project.

### Context
Read D4 in `.softfield/cards/f262-i-want-ability-to-archive-a.md`, then how f132-02 and f132-05 list the projects they draw (`.softfield/cards/f132-the-overview-shows-the-whole-factory.md`, and `factory_dashboard/overview.py`).
- `metrics.is_archived(row)` in `runner/metrics.py` says whether a project is archived.
- The cross-project notices in `overview.py` (Needs you) keep an archived project's items: leave them.

### Done when
- with coucou archived, the Overview's live lanes and the floor show no coucou, and the other projects as before
- a job of an archived project still running when it was archived still shows until it ends
- the cross-project notices still list an archived project's open items
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 7888932
logs: .softfield/var/runs/20261125-135013/f262-03-floor-leaves-archived-out
```
