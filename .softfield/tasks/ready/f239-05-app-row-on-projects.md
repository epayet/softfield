---
id: f239-05-app-row-on-projects
milestone: f239-i-want-to-be-able-to-3
difficulty: 4
depends_on: [f239-04-replan, f239-08-services-and-commit]
files:
  - factory_dashboard/projects.py
  - factory_dashboard/stacks_routes.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/templates/_partials/app_row.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
  - tests/factory_dashboard/test_stacks_routes.py
---

### Goal
Each project's plate on the Projects page shows its app: its state in words, Run or Stop, Open and Logs; a project without a stack offers to plant a card for one, and Softfield shows nothing.

### Context
The picture to build is `.softfield/cards/f239-mockup/projects-run.html` (Proposed). Read D2, D5, D6 and D7 in `.softfield/cards/f239-i-want-to-be-able-to-3.md`, then `project_cards` and `projects_page` in `factory_dashboard/projects.py`, `factory_dashboard/templates/projects.html`, `factory_dashboard/stacks_routes.py` (f239-03: `stack_of`, `app_row`, `STATE_WORDS`, `UP`), the app row partial it draws, and `stack_for`, `state`, `logs` and `StackState` in runner/stacks.py (f239-01; f239-08 adds `StackState.commit`).
- `ProjectCard` gets the app's `StackState`, or None for no stack, and a flag for Softfield; `stack_of` (not a second lookup) finds each project's stack from the registry. `stack_for` is None for Softfield too, so the flag is Softfield's repo, not a missing `[run]`. Docker missing is the state `NO_DOCKER`, with its reason in `detail`.
- Extend the partial `app_row.html` and the context `app_row` builds; the row posts, and is swapped, as f239-03 wrote it.
- Run and Stop post with htmx to the routes of D5 and swap the row; while it waits, the row shows "starting…" or "stopping…" with the dashed hazard edge `.way` already uses.
- Open is a link to `http://<the page's host>:<url_port><path>`, shown only while running; it opens in the same tab.
- Both plant buttons of D7 post to `/requests` as the Plant box in `factory_dashboard/templates/planning.html` does: `kind=plant`, `project=<that project>`, `value=` JSON `{"text": D7's text, "ask": false}`; then say "On its way" as the Plant box does. "Plant a card to fix it" shows on a crashed or update failed row; the commit is `StackState.commit` and its log lines come from `logs` in runner/stacks.py, which raises `ValueError` only for a bad service name (pass none).
- New colours or shapes join the tokens at the top of `factory_dashboard/static/dashboard.css` first; ornament never uses `--good` or `--fail`.

### Done when
- a running project's plate shows "Running", Stop, Open and Logs; a stopped one "Stopped" and Run, without Open
- a crashed one shows "Crashed" with the detail, Run, Logs and "Plant a card to fix it"; update failed shows the commit it failed on and the same plant button
- the fix plant's text holds the project, the commit and the last 30 log lines
- a project without `[run]` shows the plant button and no Run; Softfield's plate has neither
- Docker missing shows its reason on the row, and the page still draws
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
