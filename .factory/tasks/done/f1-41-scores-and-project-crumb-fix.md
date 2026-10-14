---
id: f1-41-scores-and-project-crumb-fix
milestone: f1
depends_on: [f1-37-milestone-page-fixes, f1-38-project-page-fixes]
difficulty: 2
finding: f1-cp9
files:
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/project.html
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_projects.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_projects.py
---

### Goal
`/milestones/{key}` shows the stored review and owner scores as they are on the 1–10 scale, and `/projects/{name}` has no empty crumb.

### Context
Read `factory_dashboard/templates/milestone.html` (the Results list), `factory_dashboard/templates/project.html`, `tasks/done/f1-37-milestone-page-fixes.md` and `tasks/ready/f1-23-findings-json.md`. `write_fixture`, `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py` stay untouched; extend your own conftest functions.
- Facts: f1-23 stores `milestones.review_score` and `owner_score` as 1–10 (`--score N`, review `"score": 1-10`), but the template prints `score * 10` + `/10`, so a stored 7 shows `70.0/10`. No test sets a score: the fixture writes none, so only the dash is ever rendered and the f1-37 Done when line "the two scores show the values stored" is untested. The same f1-37 left the Done when `<li>` and the run filter's "a run with no jobs in the milestone" case untested too.
- Facts about the project page: `project` in the context is the project's name (a string, from `factory_dashboard/app.py`), so `{{ project.name }}` in the `crumbs` block of `factory_dashboard/templates/project.html` renders an empty `<span>`; the base template already prints the project crumb. The title test and breadcrumb test pass because they match the base's link.

### Done when
- the review score and the owner score show the stored value with one decimal and `/10` (a stored 7 shows `7.0/10`), a dash if none
- the project page renders no empty crumb element
- tests: a milestone with both scores set shows `7.0/10` and `8.5/10` each in its own `<dt>`/`<dd>`, and one with none shows dashes; the Done when items are asserted as `<li>` inside the section; `test_timeline_run_filter` also asserts 0 bars for a run with no jobs in the default milestone; the project crumb test asserts the crumbs area holds exactly one element for the project
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1127
gate_failures: []
tokens: 1633078
```
