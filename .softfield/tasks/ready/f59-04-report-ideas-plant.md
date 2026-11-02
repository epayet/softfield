---
id: f59-04-report-ideas-plant
milestone: f59-periodic-review-of-the-factory
difficulty: 3
depends_on: [f59-02-reports-page, f164-03-idea-plates-with-plant]
files:
  - factory_dashboard/reports.py
  - factory_dashboard/templates/reports.html
  - factory_dashboard/templates/_partials/idea.html
  - tests/factory_dashboard/test_reports.py
tests:
  - tests/factory_dashboard/test_reports.py
---

### Goal
Each quoted idea of a weekly report shows F164's plate with Plant and Plant and ask the lead, and once planted links to its card.

### Context
Read `.softfield/cards/f59-periodic-review-of-the-factory.md` (D7) and `.softfield/cards/f164-i-like-reading-the-milestone-reviews.md` (D2 to D5).
- Use the partial `factory_dashboard/templates/_partials/idea.html` and the state lookup of F164 (f164-02, f164-03) as they are; the idea's id is `report-<monday>/<n>`, its text ends "From the report of the week of 19 Oct."
- Its area and project: an idea under "Ideas for the factory" is factory and goes to the factory's own project; under "Ideas for <project>", that project.

### Done when
- a report's quoted idea shows both buttons; Plant posts a `plant` request with the idea's text, `ask` false, its area and its id as `from`
- an idea already planted links to its card; one on its way shows F164's dashed plate, after a reload too
- an idea under "Ideas for travel-companion" posts to travel-companion
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
