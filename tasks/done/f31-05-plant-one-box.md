---
id: f31-05-plant-one-box
milestone: f31-when-i-click-on-approve-plan
difficulty: 5
depends_on: [f31-03-point-outcomes, f13-01-planted-idea-shows-at-once, f14-01-change-request]
agent: lead
files:
  - runner/planner.py
  - runner/requests.py
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
Planting takes one box of text.

### Context
Read `docs/milestones/f31-when-i-click-on-approve-plan.md` D7. In `runner/planner.py`: `planting`, `_plant_data`, `_MAX_TITLE`, `slug` and `seed_card`; in `runner/requests.py`: `_plant` and f14-01's `change`; in `factory_dashboard/planning.py`: `coming`; in `factory_dashboard/templates/planning.html`: the `#plant` form (f13-01's `#plant-row`).
- The value `{"text", "area"}`: the heading is the text's first words cut at a word under 60 characters (an ellipsis when cut), the slug its first six words as today, the whole text the card's Notes and the thread's first message. `{"title", "thoughts"}` still plants as today.
- A `change` (f14-01) on a waiting plant takes the new `text` too.
- The form: one `textarea` ("What's on your mind?"), the area, and the two buttons as they are (Plant, Plant and ask the lead: the value's `ask`, ADR 20 item 8). The lead names the card in its first reply, whenever the owner sends it.

### Done when
- a 300-character note with no title is planted: its heading is its first words under 60 characters, its Notes the whole text, and its thread's first message the whole text
- a `{"title", "thoughts"}` plant still plants as today
- the form has one text box; both buttons work at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: built by the lead in a terminal session (owner, 2026-10-08), before f31-03, f13-01 and f14-01; the lead naming the card stays with f31-03, a change of a waiting plant with f14-01
```
