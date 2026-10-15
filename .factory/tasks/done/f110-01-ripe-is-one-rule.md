---
id: f110-01-ripe-is-one-rule
milestone: f110-i-don-t-understand-why-there
depends_on: []
difficulty: 4
files:
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A card the board calls ripe is ripe on the line's field too, so its page has the Sign off button and the desk lists it: tickets set aside or removed count for no stage.

### Context
Read `factory_dashboard/line.py` (`_field`, `_states`), `factory_dashboard/board.py` (`_milestone_stage`, `_OFF`) and `.factory/cards/f110-i-don-t-understand-why-there.md` (D1). Follow the worked examples: `test_a_set_aside_ticket_keeps_no_card_from_ripening` in `tests/factory_dashboard/test_board.py`, `test_a_card_ripens_only_once_its_review_is_written` in `tests/factory_dashboard/test_line.py` and `test_a_ripe_milestone_shows_its_signoff_button` in `tests/factory_dashboard/test_milestones.py`.
- The board leaves a milestone's set-aside (`later`) and removed tickets out before it asks "is every ticket done?". `_field` keeps them in `states`, so a reviewed milestone with every other ticket done is neither in `rows` nor in `ripe`: it is on the board as ripe with no button on its page (the button and the desk read `field["ripe"]`).
- Leave those two states out of a milestone's `states` in `_field`, as the board does. `field["later"]` and `field["seeds"]` still list the set-aside tickets, and a row's `total` no longer counts them.
- Don't change the board's rule or the runner.

### Done when
- a milestone with its review's sheet stored, one ticket done and one set aside is in `field["ripe"]`, and not in `field["rows"]`
- the same with a removed ticket in place of the set-aside one
- a milestone whose only tickets are set aside is in neither `ripe` nor `rows`
- without its sheet, the first milestone is in `rows` with `done` 1 and `total` 1
- the set-aside ticket is still in `field["later"]`
- the page of the first milestone has the Sign off button (`id="signoff-button"`)
- the listed tests pass, and fail without the change

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 5281
gate_failures: ['stopped', 'stopped']
tokens: 2054863
```
