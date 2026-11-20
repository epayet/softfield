---
id: f132-10-fix-one-project-cells
milestone: f132-the-overview-shows-the-whole-factory
difficulty: 2
depends_on: [f132-09-fix-jobs-runs-timeline-plates]
finding: f132-cp8
files:
  - factory_dashboard/templates/jobs.html
  - factory_dashboard/templates/runs.html
  - factory_dashboard/templates/timeline.html
tests:
  - tests/factory_dashboard/test_jobs.py
  - tests/factory_dashboard/test_runs.py
  - tests/factory_dashboard/test_timeline.py
  - tests/factory_dashboard/test_app.py
---

### Goal
With one project, Jobs, Runs and the Timeline's jobs table have no Project cell in any row, so every row's cells line up under its headers; the picker tests check what the page does.

### Context
f132-09 hid the `<th>Project</th>` header when `many_projects` is false, but each body row still prints its Project `<td>` (`<td class="proj">…{{ job.project }}</td>` in `jobs.html`, `{{ run.project }}` in `runs.html`, `{{ bar.project }}` in `timeline.html`): one more cell than headers, every column shifted one to the right. The one-project tests read only the `<th>` rows, so they pass.
- Guard the whole `<td>` with `many_projects`, the way the `<th>` is.
- The one-project tests count each body row's cells against the header's, and assert no cell holds the project name.
- In `tests/factory_dashboard/test_app.py` (f132-08): `test_changing_the_picker_reloads_with_the_project` asserts `"coucou" in html` and `"other" in html_other`, which any page with the word passes; make it read the `selected` option of each response. `test_the_bay_group_uses_rule_tokens` matches `<span class="bay-group">(.*?)</span>`, which ends at the picker's own closing `</span>`, so it never reads the tabs; read the whole group (up to its `</nav>`) or drop the test.

### Done when
- one project only: each body row of `/jobs`, `/runs` and `/timeline` has as many cells as its header, and none holds the project's name
- two projects: unchanged (each row's Project cell holds that row's plate)
- the picker test reads the chosen option of the page it loads
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
