---
id: f142-02-fix-own-project-ids-notify-twice
milestone: f142-why-am-i-not-getting-notifications
difficulty: 3
depends_on: []
files:
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_app.py
finding: f142-why-am-i-not-getting-notifications-C1-1
---

### Goal
Fix a checkpoint finding on f142-01-notify-every-project: the same open item gets a different id on its own project's page than on another project's page, so the owner is notified twice.

### Context
By the lead at a checkpoint, on the merge of `.softfield/tasks/done/f142-01-notify-every-project.md`. What was found is under Finding:
- f142-why-am-i-not-getting-notifications-C1-1, should-fix: `_live_context` in `factory_dashboard/overview.py` and the tests of `data-notices`.

### Finding
f142-why-am-i-not-getting-notifications-C1-1: f142-01 asked that every id in `data-notices` start with its project's name and a slash (`softfield/owner-129`). `_live_context` keeps the page's own project's ids bare (`owner-129`) and gives the others `<project>/owner-129`. `compare` keeps one `notify:seen` key, so an item of project B seen from a page on A is stored as `B/owner-1`; opening a page on B then sees `owner-1` as new and notifies again. The test `test_data_notices_ids_start_with_project_name` in `tests/factory_dashboard/test_overview.py` does not check this: it accepts any bare `owner-` id, and `test_data_notices_own_project_no_prefix` only asserts inside an `if`, so it passes with no notice. `test_compare_uses_one_key_not_per_project` in `tests/factory_dashboard/test_app.py` never loads a page on the other project ("switch back to coucou" re-polls the same page), so it does not test what its docstring says.

### Done when
- every id in `data-notices`, the page's own project's included, starts with its project's name and `/`, and the own project's titles still carry no project name
- a test loads `/live?project=coucou` then `/live?project=other` with the same open item on `other`, and the item's id is the same in both
- a browser test of a page on A, then a page on B (its `data-project` changed as the bundled-link test does) with the same open items shows no second notification
- the weak tests named above assert on content with no `if` that lets them pass empty
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3700
gate_failures: []
tokens: 4534625
```
