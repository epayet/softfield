---
id: f154-01-stage-says-what-next
milestone: f154-what-s-the-difference-between-planted
agent: lead
difficulty: 4
depends_on: [f152-01-review-step-on-the-card]
files:
  - factory_dashboard/board.py
  - factory_dashboard/milestones.py
  - factory_dashboard/line.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/_partials/stage_icon.html
  - factory_dashboard/static/board.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The board's Planted and Growing stages become one Planted column in the runner's order, where any card can be moved before any other; a card with work started says "growing" on itself, and each stage's head says what it means and what comes next.

### Context
Read `.softfield/cards/f154-what-s-the-difference-between-planted.md` (D1–D4) and the mock-up to build, `.softfield/cards/f154-mockup/stage-words.html` (Proposed).
- `factory_dashboard/board.py`: `STAGES`, `WORDS`, `PLACED`, `Card`, `_milestone_stage`, `_bug_stage`, `_card_note` and the places `running=` is set; the order and the "on its way" places are counted per stage, so one column gives one line of places.
- The runner's `reorder` (`_reorder` in `runner/requests.py`) already takes the whole board as one list of keys: change nothing in `runner/`.
- `factory_dashboard/line.py` reads `stages["planted"] + stages["growing"]` for the floor's rows; `factory_dashboard/milestones.py`'s `how_it_grew` puts the started date on growing.
- In `factory_dashboard/static/dashboard.css`: `#stage-growing`, `.at-growing`, `#stage-growing .card` and the phone order under 900 px. The tag uses the existing tokens only.
- F152's review step (f152-01, built before this one: `Card`'s review field, the `card-review` element, the Stage line on the card's page) is shown on growing cards whose tickets are all done; it now shows on planted cards with `started` true whose tickets are all done, with the same words.
- Every test that names a growing stage or "in the factory" changes with it: search `tests/factory_dashboard/` for `growing`.

### Done when
- `STAGES` is seed, sprouting, planted, ripe, harvested, and the board page shows those five plots and columns
- a milestone with a ticket started and one not done is in Planted with `started` true, the "growing" tag and the class `started`; one with no ticket started is in Planted with neither; a running bug ticket is in Planted and started
- the planted cards are numbered #1… as one line by priority, and a reorder's "on its way" places count across all of them
- the Planted head reads "in line for the factory, #1 first · N, M growing" and "Next every ticket done, then Claude reviews it"; each stage of D2 shows its meaning and next step, Harvested no next line
- a started card's page says "Stage Planted: in line for the factory" and its stage steps show "growing since" its started date on Planted
- the factory floor's rows hold the same cards as before
- a started planted card with every ticket done still shows F152's review step; a planted card not started shows none
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
