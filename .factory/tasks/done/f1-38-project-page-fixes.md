---
id: f1-38-project-page-fixes
milestone: f1
depends_on: [f1-29-project-page]
difficulty: 3
finding: f1-cp6
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/project.html
  - tests/factory_dashboard/test_projects.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
`/projects/{name}` keeps the top bar and breadcrumbs right, and lists milestones and runs the way f1-29 asked, with tests that read what the page shows.

### Context
Read `factory_dashboard/projects.py`, `factory_dashboard/templates/project.html`, `factory_dashboard/templates/base.html`, `render` in `factory_dashboard/app.py` and `tests/factory_dashboard/test_projects.py`; f1-29's spec is `tasks/done/f1-29-project-page.md`. `write_fixture`, `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py` stay untouched; extend `write_project` in `tests/factory_dashboard/conftest.py`.
- Facts about the page: `project_page` passes `"project": meta` (a `ProjectMeta`) in the context, which replaces the project name string that `render` puts there and that `factory_dashboard/templates/base.html` uses. So the `<title>` reads `coucou · Project · ProjectMeta(name=…)`, the breadcrumb link text is the dataclass repr and its href is the urlencoded repr, and the top bar's `name == project` never matches, so no project is selected.
- The milestone list sorts `status IS 'done'` first and `started` second, so an in-progress milestone comes before a newer done one; f1-29 asked for newest first. It shows the key and status only, not the title that `milestone_summaries` selects. The runs list shows `run_dir` only; `ended` is selected and not shown, and the list is every run, f1-29 asked for the last ones.
- Facts about the tests: the milestone test finds "F2" before "F1" in the section text but never reads a status or title; the runs test checks two `href`s in the whole page, not their order or section; no test reads the title, the breadcrumbs or the top bar.

### Done when
- the page's title, breadcrumb text and link and top-bar selection show the project's name (`coucou`), not an object
- milestones are listed newest first by `started` whatever their status, each with its key, title and status
- runs are listed newest first, each with when it ended, and only the last 10
- tests: the title, the breadcrumb text and href, and the selected top-bar option are asserted; the milestone section is read in order with each key, title and status; the runs section is read in order (and with more than 10 runs, only the newest 10 show); the fixture has an in-progress milestone newer than a done one
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1062
gate_failures: []
tokens: 1154746
```
