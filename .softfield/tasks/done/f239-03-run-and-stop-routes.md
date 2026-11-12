---
id: f239-03-run-and-stop-routes
milestone: f239-i-want-to-be-able-to-3
agent: lead
difficulty: 5
depends_on: [f239-01-run-config-and-stacks]
files:
  - factory_dashboard/stacks_routes.py   # the routes: the layout gate wants a module for the test file
  - factory_dashboard/app.py
  - tests/runner/test_look.py             # the dashboard's POSTs: ADR 46 item 6 adds two
  - runner/stacks.py
  - factory_dashboard/templates/_partials/app_row.html
  - runner/instructions/run-stack.md
  - tests/factory_dashboard/test_stacks_routes.py
tests:
  - tests/factory_dashboard/test_stacks_routes.py
---

### Goal
The dashboard starts and stops a project's app at once, behind the dashboard's own guard, and the recipe of what a project's stack needs is written down for the cards that will build one.

### Context
Read ADR 46 items 1, 5, 6 and 8 and D5 and D7 in `.softfield/cards/f239-i-want-to-be-able-to-3.md`, then `from_the_dashboard` in `factory_dashboard/requests.py`, `projects_page` in `factory_dashboard/projects.py` and `start`, `stop` and `state` in `runner/stacks.py` (f239-01). Tests first: this is the dashboard's first write that isn't a request row.
- `POST /projects/{name}/run` and `/stop` answer 403 without the guard, 404 for a name not in `projects_in_order` or with no `[run]`, and otherwise call `start` or `stop` and answer the app row re-drawn from `state` (the partial: words and buttons only; f239-05 draws it as the mock-up).
- `runner/instructions/run-stack.md`: what ADR 46 item 1 asks of `compose.yaml`; how to pick the port (8100–8199, not used by another project's `compose.yaml`, free on the machine); `[run]` in `.softfield/project.toml`; the main service runs its migrations before it serves (for Django, `migrate` then the server, in its `command`); moving existing data into `~/.local/share/softfield/data/<project>` as a copy; and that `docker compose up -d` in the repo must work without the factory. Plain words, under 60 lines.

### Done when
- a POST without `HX-Request`, or from another origin, answers 403 and never calls `_docker`
- an unknown project, and Softfield, answer 404
- a guarded Run on a project with `[run]` calls `start` once and answers its row saying Starting or Running
- `runner/instructions/run-stack.md` exists and names `APP_PORT`, `APP_DATA`, `[run]`, `restart: unless-stopped` and the migrations at start
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
