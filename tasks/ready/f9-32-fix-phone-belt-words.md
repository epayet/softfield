---
id: f9-32-fix-phone-belt-words
milestone: f9-line-polish
depends_on: []
difficulty: 4
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_overview.py
finding: f9-22-floor-words
priority: 40
area: factory
---

### Goal
On the phone, the belts that had words ("developer", "lead's work", "merged"...) keep them and gain "today"; only the belts that were already bare numbers say "7 today".

### Context
Read `factory_dashboard/static/factory.js` (`belt`, `PHONE_BELTS`), `tests/factory_dashboard/test_line.py` (`test_a_phone_draws_every_station_with_its_crates_and_belts`) and `tests/factory_dashboard/test_overview.py`.
- f9-22 set `short: true` on almost every `PHONE_BELTS` entry. A `short` belt drops its label, so the phone lost "developer · 7", "merged · 7" and "back to the lead · 2", and the phone test was edited to expect a bare "7 today" for `checks→merged`, which was not a short belt. The ticket asked for "7 today" only on belts that were already short.
- Restore each `PHONE_BELTS` entry's `short` to what it was before f9-22 (`git show e60c3f49b -- factory_dashboard/static/factory.js` shows the old lines), and put the phone test back to `merged · {merged} today`.
- f9-22 also left Done-when points with no test that fails without them; add them:
  - Planting reads "ideas you're planning", "with the lead" and "N in talks" (N from the document's planting count, not a fixed number);
  - the legend contains "faded, dashed: waits for another ticket" and "a replay counts its own day";
  - the overview savings heading reads "so far on F6" for a milestone, and the floor's heading has no "refreshes";
  - a developer crate's computed fill differs from the lead crate's and from the checks light's, in both themes.
- In `factory_dashboard/static/dashboard.css` the f9-22 lines for `--good` / `--dev` gained a stray leading space; take it out.

### Done when
- on the phone, `checks→merged` reads "merged · N today", `queue→developers` reads "developer · N today", and a belt that was bare (`seeds→planting`) reads "N today"
- the four extra checks above exist and fail without the f9-22 change
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
