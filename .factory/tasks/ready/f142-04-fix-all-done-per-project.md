---
id: f142-04-fix-all-done-per-project
milestone: f142-why-am-i-not-getting-notifications
difficulty: 3
depends_on: []
files:
  - factory_dashboard/static/notify.js
tests:
  - tests/factory_dashboard/test_app.py
finding: f142-why-am-i-not-getting-notifications-F2
---

### Goal
Moving between projects' pages never notifies "All work done" again: what a browser saw of all the work being done is kept per project, inside the one `notify:seen` key.

### Context
Read `compare` in `factory_dashboard/static/notify.js`, then `test_compare_uses_one_key_not_per_project` in `tests/factory_dashboard/test_app.py` (the worked example: it loads a page on another project by swapping in `/live?project=other`).
- Today `notify:seen` holds one `done` for the whole dashboard. A page on a busy project (`data-all-done="false"`), then a page on an idle one (`"true"`) within 60 s, notifies "All work done", and does again at each switch back and forth.
- Keep `done` as an object by project name (`{"coucou": false, "other": true}`), and notify only when the page's project's own `done` turns true. A stored `done` that is still a plain true or false (from before this change) counts as no project seen: no notification on that look.
- The ids (`ids`), the 60-second rule and the bundling don't change.

### Done when
- a page on project A (not all done), then a page on project B (all done, nothing new): no notification
- back on A, then on B again within 60 s: still no notification
- a page on A whose work ends (`data-all-done` from false to true on A): one "All work done", as today
- a stored `notify:seen` with `done: false` (the old shape), then a look with all done: no notification and no error
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
