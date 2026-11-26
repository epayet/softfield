---
id: f302-01-edit-an-idea-first
milestone: f302-on-factory-suggestions-i-can-plant
difficulty: 3
files:
  - factory_dashboard/templates/_partials/idea.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_thread.py
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
A review's idea plate gets an "Edit first" button: it turns the idea's words into a box the owner can change, and Plant and Plant and ask the lead then plant those words.

### Context
Read `.softfield/cards/f302-on-factory-suggestions-i-can-plant.md` (Done when, D1 to D5). The picture to build is `.softfield/cards/f302-mockup/edit-before-planting.html` (Proposed).
- The plate is `factory_dashboard/templates/_partials/idea.html`; its buttons' `hx-vals` come from `idea_vals` in `factory_dashboard/milestones.py`, whose `value` is a JSON string `{text, ask, area, from}`. Leave `idea_vals` and `runner/` as they are.
- While the box is open, each Plant button's `hx-on::config-request` parses `event.detail.parameters.value`, sets its `text` to the box's words, and writes it back (D3). The existing `hx-on::before-request` (on its way at once) stays.
- The box starts with the `text` the plant sends today (D4), so the partial needs it: read it from the button's own `hx-vals`, or pass it in; don't build the source sentence twice.
- Follow the browser tests `test_pressing_plant_turns_the_plate_on_its_way_at_once_and_posts_it` and its neighbours in `tests/factory_dashboard/test_thread.py`, with their `_sheet` and `_open` helpers.
- CSS goes beside F164's `.idea …` rules in `factory_dashboard/static/dashboard.css`, with the existing tokens only.

### Done when
- a plate that can still be planted shows Edit first after Plant and ask the lead and Plant; a planted or on-its-way plate shows none of them
- pressing Edit first hides the quote and Edit first, shows a box holding the plant's text ("… From F28's review." in the test), the tag's "your words" and the lead's words with "Put them back"
- after editing the box, pressing Plant stores one `plant` request whose `text` is the edited words and whose `ask`, `area` and `from` are the idea's; Plant and ask the lead the same with `ask` true
- pressing Plant without Edit first still stores the lead's words, as today
- an emptied box disables both Plant buttons; "Put them back" restores the original text
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
