---
id: f198-01-plant-above-coming
milestone: f198-keep-the-plant-an-idea-at
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On `/planning`, Plant an idea comes straight under the two tiles and never moves when a plant is on its way; Coming seeds sits right under the box.

### Context
Read `.softfield/cards/f198-keep-the-plant-an-idea-at.md` (Decisions) and `factory_dashboard/templates/planning.html`. The picture to build is `.softfield/cards/f198-mockup/plant-first.html`.
- `#live-desk-coming` (with `#desk-coming` in it) moves out from above the flex row into a new column, the row's first child, after `#plant-row`: `#plant-row` then `#live-desk-coming`, and `#live-desk` stays beside the column.
- The column takes over the form's `flex: 1 1 280px; min-width: 0` and stacks its children with a 14px gap. `#desk-coming` loses its `margin-top`.
- `#plant-row` and `#live-desk-coming` stay separate, each drawn again on its own: a poll of Coming must never redraw a half-typed note.
- Update the script's "Coming sits above the box" comment. Rename `test_coming_then_plant_then_the_desk_then_archived` to say the new order, and follow the browser-test pattern of the tests around `test_after_a_plant_is_sent_the_fresh_box_is_at_four_row_height`.
- **Change only where these parts sit: no item's words, link, condition or poll changes.**

### Done when
- with a plant on its way, `id="plant"` comes before `id="desk-coming"`, which comes before `id="desk"`, and `id="archived"` is still last; with nothing on its way there is no `desk-coming`
- in a browser, at 390 px and at 1280 px wide, `#plant`'s top is the same before and after a plant is sent, and `#desk-coming` shows below `#plant`
- at 1280 px, `#desk-coming` has the same left edge as `#plant` and `#desk`'s top doesn't move when it appears; at 390 px, `#desk-coming` is above `#desk`
- a note half typed in the box is still there after Coming's 5-second poll
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 1673
gate_failures: ['all-tests', 'all-tests']
tokens: 2899180
```
