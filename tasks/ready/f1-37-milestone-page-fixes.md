---
id: f1-37-milestone-page-fixes
milestone: f1
depends_on: [f1-13-milestone-page]
difficulty: 3
finding: f1-cp5
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_timeline.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_timeline.py
---

### Goal
`/milestones/{key}` shows the milestone's Done when and its two scores truthfully, and the tests read the text the page shows.

### Context
Read `factory_dashboard/milestones.py`, `factory_dashboard/templates/milestone.html`, `tests/factory_dashboard/test_milestones.py`; f1-13's spec is `tasks/done/f1-13-milestone-page.md`. `write_fixture`, `test_queries.py` and `test_overview.py` stay untouched; extend your own conftest functions.
- Facts about the page: the template reads `milestone.done_when_html`, but `done_when_html` is a template variable beside `milestone`, not an attribute of it, so Jinja renders nothing: the "Done when" heading shows with an empty body even when `done_when` is set. The outcome is printed as plain text, not through `_to_html` like the other parts. The "Review score" line prints `milestone.results.claude.dollars` (a dollar amount), not a score; "Owner score" is a literal dash. The `milestones` row has `review_score` and `owner_score` columns (see `runner/metrics.py`); check whether `upsert_milestone` writes them. The findings per severity appear in both Results and Findings.
- Facts about the tests: no milestone-page test reads any text from the sign-off, the outcome or Done when; the fixture sets them, so a page that drops them all still passes. The savings test checks three fragments of the template's own wording, not the dollar figures. The ticket and run tests check one `href` in the whole page, not that the tickets section lists exactly the milestone's tickets. The order test ignores sections not in its list. `test_timeline_run_filter` asserts 0 bars for a run of another milestone, which any broken filter also gives; `test_timeline_milestone_select_shows_filter` and `test_timeline_default_page_shows_latest_milestone` are the same test twice.

### Done when
- the Done when text of a milestone shows on its page, lists as `<li>`, under the heading
- the outcome renders like the other text parts
- the review score and the owner score show the values stored in `milestones` (a dash if none), never a dollar amount
- tests: each sign-off part, the outcome and the Done when are asserted by their text, inside their own section; savings by their dollar figures; the tickets section lists exactly the milestone's tickets; the run filter is tested with a run that has jobs in the default milestone (only that run's bars appear) and one that has none; the duplicate timeline test is dropped or made different
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
