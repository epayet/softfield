---
id: f142-01-notify-every-project
milestone: f142-why-am-i-not-getting-notifications
difficulty: 3
depends_on: [f114-07-fix-rejected-worker-notifications-lose, f114-08-fix-bundled-link-test-accepts, f114-09-fix-notification-tests-do-not, f114-10-fix-fallback-onclick-test-always-passes]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/static/notify.js
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_app.py
---

### Goal
A dashboard page open on any project notifies for what needs the owner on every project, each notice named with its project when it isn't the page's.

### Context
Read `.factory/cards/f142-why-am-i-not-getting-notifications.md` (D1, D2), then `needs_you`, `notices` and `_live_context` in `factory_dashboard/overview.py`, `projects_in_order` in `runner/metrics.py`, and `compare` in `factory_dashboard/static/notify.js`. Follow the worked examples F114 left: the `data-notices` tests in `tests/factory_dashboard/test_overview.py`, and the `FAKE_NOTIFICATION` tests of `compare` in `tests/factory_dashboard/test_app.py`.
- `data-notices` keeps the page's project's notices as they are, and adds, for every other project `projects_in_order` gives, a notice for each of its open `owner_items`, worded by `notices` with that project's card titles, with "<project name>: " before the title and the link's `?project=` set to that project.
- The other projects bring their stored items only: the stopped runner, the idle queue and `data-all-done` stay the page's project's.
- Every id in `data-notices` starts with its project's name and a slash (`softfield/owner-129`).
- `compare` keeps what it saw under one `localStorage` key for the dashboard (`notify:seen`), not one per project; the 60-second rule and the bundling of several new ids don't change.

### Done when
- a page on project A with an open item on project B: `data-notices` has B's item, titled "B: " then its usual title, its link carrying `?project=B`
- a forgotten project's items are not in `data-notices`
- the page's own project's notices keep their titles, without a project name
- every id in `data-notices` starts with its project's name and `/`
- a page on project A, then a page on project B with the same open items: no notification on B
- a new item on project B while a page on A is open: one notification
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
