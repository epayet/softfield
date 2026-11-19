---
id: f122-06-start-plate-once
milestone: f122-new-project-from-the-projects-page
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/projects.html
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
Pressing "Start it" on the Projects page draws the new project's on-its-way plate once, however long the request waits for the runner.

### Context
Read the second script at the bottom of `factory_dashboard/templates/projects.html` (Start a project, F122 D6) and `factory_dashboard/templates/_partials/request.html`.
- The bug, seen by the owner on 2026-11-19: after Start, the answer swapped into `#start-sent` is the request's "Asked" line, which polls `/requests/<id>` every 5 s with htmx. `#start-sent` is inside `#start-form`, so each poll's `htmx:beforeRequest` bubbles up to the form's listener, which appends one more plate every 5 s until the runner takes the request. The same poll also goes through the form's `htmx:configRequest` listener, which rewrites its parameters.
- The example to follow is in the same file: the order form's listeners start with `if (event.target !== form) return;`. Give both of the start form's htmx listeners that guard.

### Done when
- the start form's `htmx:configRequest` and `htmx:beforeRequest` listeners act only on the form's own request, as the order form's do
- the rendered page's start script carries that guard for both listeners, and nothing else on the page changes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 786
gate_failures: []
tokens: 169415
```
