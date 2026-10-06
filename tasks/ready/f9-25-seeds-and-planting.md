---
id: f9-25-seeds-and-planting
milestone: f9-line-polish
depends_on: [f9-24-tap-sheet]
difficulty: 4
files:
  - factory_dashboard/line.py
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The field's first two stations show real things: Planting counts the cards being planned with the owner, and tapping the seeds opens the sheet with the set-aside tickets listed, each a link.

### Context
Read `_field` in `factory_dashboard/line.py` (its `seeds` count and `"planting": 0`), `desk` in `factory_dashboard/planning.py` (how idea cards and threads are found, F6 D6), and in `factory_dashboard/static/factory.js` `seeds`, `planting` and the crate card (`showCard`, the sheet from f9-24). Then the field tests in `tests/factory_dashboard/test_line.py`.
- `"planting": 0` is a placeholder: nothing ever counted it. Planting is the cards whose `milestones.state` is idea or planning, plus any card with a `planner_threads` row and no ticket yet. Each card counts once.
- The field gains `later`: the set-aside tickets (ticket state `later`), each `{ticket, title}`, by id. `seeds` stays their count.
- The owner (2026-10-06): "the seeds set aside are not really navigable on mobile". Tapping the seeds opens the sheet (f9-24's card) listing them: id and title, each a link to `/tickets/<id>` keeping `?project=`, and at the end "All set-aside tickets" to `/tickets#later`. On desktop the same card opens under the floor.
- Titles go in as text nodes, never HTML (f3-F1).

### Done when
- with two idea cards, one planning card with a thread and one building card with a thread in the fixtures, `planting` is 3
- `later` lists the set-aside tickets with their titles, and `seeds` equals its length
- tapping the seeds opens the sheet with one link per set-aside ticket and the "All set-aside tickets" link
- a title holding `<b>` shows as text
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
