---
id: f1-13-milestone-page
milestone: f1
depends_on: [f1-12-milestones-list, f1-35-timeline-milestones-fixes]
difficulty: 5
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
`/milestones/{key}` shows one milestone: what was expected, what changed, and how the work went.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). The list is in `factory_dashboard/milestones.py`, its router already registered in `factory_dashboard/app.py`; add the page there. Numbers from `factory_dashboard/queries.py`. `write_fixture`'s numbers are pinned by `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py`: put the rows your page needs in a function of your own (as `write_live` is), not among f1's or m4's tickets and jobs.
- Facts: `runs` has no milestone column: a milestone's runs are the runs of its jobs (`jobs.milestone_id`). Nothing writes `review_score` or `owner_score` yet (f1-23 will), nor a finding's `file`, `line` or `ticket_id`: an empty one shows a dash.
- **In this order** (D8 in `docs/milestones/f1.md`, the owner's): the outcome and Done when; what changed and how to test it; what next; left for later and how the work went; then results (pass rate, attempts, escalations, review rounds, both scores), savings (doing it itself against supporting, then net, in dollars with tokens underneath), its tickets with their results (links), its runs (links to `/runs/{run_dir}`), and its findings.
- The text parts come from `milestones.signoff` (JSON with `changed`, `how_to_test`, `what_next`, `later`, `lessons`), `outcome` and `done_when`; render their Markdown lists and bold as HTML. A part that's missing shows "Not written yet".
- An unknown key answers 404.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- the page shows its sections in D8's order (check the order of their headings in the HTML)
- savings show both parts and the net, in dollars
- a milestone without a sign-off shows "Not written yet" for those parts
- its tickets and runs link to their pages
- an unknown key is a 404
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
