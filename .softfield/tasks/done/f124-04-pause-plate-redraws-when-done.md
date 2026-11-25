---
id: f124-04-pause-plate-redraws-when-done
milestone: f124-pause-one-project-from-the-projects
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/projects.html
tests:
  - tests/factory_dashboard/test_projects.py
finding: f124-pause-one-project-from-the-projects-F2
area: factory
---

### Goal
Once the runner has taken a project's Pause or Resume, that project's plate on the Projects page redraws by itself: "Paused by you since HH:MM" with its Resume (or Pause again), without the owner reloading the page.

### Context
- `factory_dashboard/templates/projects.html`: the Pause / Resume button posts into `#pause-sent-<name>`; `factory_dashboard/templates/_partials/request.html` polls there every 5 s and, once the request is done, swaps in `<p class="request done">`. Today the button then stays "Pausing…" and the on-its-way line stays until a reload.
- Redraw that one plate only (fetch `/projects` and replace its `li.proj[data-key="<name>"]`, e.g. `htmx.ajax` with `select`), never the whole page: a reload would lose a new order the owner has dragged but not sent.
- Listen for the done swap with `htmx:afterSwap` guarded on its own target, as `test_the_start_form_htmx_listeners_guard_on_their_own_target` in `tests/factory_dashboard/test_projects.py` asks of the start form's listeners.
- Worked example of a browser test: `test_pressing_pause_turns_button_to_pausing_and_dashed` in `tests/factory_dashboard/test_projects.py`; after the click, set the project's `paused` (`metrics.set_project_paused`) and finish the request (`metrics.finish_request` or an `UPDATE owner_requests SET done`) as the runner would, then wait for the poll.

### Done when
- after Pause is pressed and the runner finishes the request, the plate shows "Paused by you since HH:MM.", its hazard edge (`li.proj.held`) and a Resume button, with no on-its-way line, without a reload
- the same for Resume: the plate goes back to a Pause button, without the paused line
- a new order dragged but not sent on another plate is still shown after the redraw
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 7627000
logs: .softfield/var/runs/20261124-231522/f124-04-pause-plate-redraws-when-done
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
