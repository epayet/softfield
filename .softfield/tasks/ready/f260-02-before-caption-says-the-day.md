---
id: f260-02-before-caption-says-the-day
milestone: f260-the-before-pictures-should-be-taken
difficulty: 2
depends_on: [f260-01-keep-the-before-data]
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
On a card's page, a before picture drawn on the data kept at the card's first merge says from which day that data is.

### Context
Read D3 in `.softfield/cards/f260-the-before-pictures-should-be-taken.md`. In the card's list of pictures (shots.json, `LIST_FILE` in `runner/shots.py`), a before picture drawn on the kept data has `"data": "YYYY-MM-DD"` beside `state` and `reason`. The page reads the pictures in `_shot_pictures` and `shots_panel` (`factory_dashboard/milestones.py`) and writes the caption "Before · at the card's start" in `factory_dashboard/templates/milestone.html`. Format the day with the module's own `_date`. Follow `test_a_before_recorded_as_new_says_the_page_did_not_exist` in `tests/factory_dashboard/test_app.py`.

### Done when
- a page whose before pictures carry `"data": "2026-11-05"` captions its Before "Before · at the card's start, on the data of" followed by that day in the page's date format
- a page whose before pictures have no `data` keeps "Before · at the card's start"
- a `data` value that isn't a date shows no date and doesn't break the page
- the After caption is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
