---
id: f206-01-dev-view-sees-started-tickets
milestone: f206-developer-is-curre-tly-working-on
difficulty: 3
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
On the board's developer's view, a card whose developer ticket has started says so, instead of "lead only".

### Context
Read `.softfield/cards/f206-developer-is-curre-tly-working-on.md` (D1 to D4). F146's rules for the view are in `.softfield/cards/f146-some-kind-of-view-or-toggle.md`.
- `factory_dashboard/board.py`: `_dev_work` counts only tickets whose state is `ready`, and `_dev_resolver` names any dependency that isn't ready as lead work. `DevWork` gets the new fields, and `_developer_totals` counts the running tickets.
- `factory_dashboard/templates/board.html`: the `dev_tag` macro holds the card's words, and the legend at the bottom of the field says "faded: lead only".
- Follow `_three_looks` and `test_each_planted_card_says_what_it_holds_for_developers` in `tests/factory_dashboard/test_board.py`; `_tickets` there takes each ticket's state.
- No CSS changes: the lit and faded looks stay as they are.

### Done when
- a card with a running developer ticket and a ready lead ticket is lit and reads "developers: working on f70-01 · then the lead's f70-02"
- a card with a running developer ticket and a ready developer ticket that depends on it is lit and reads "developers: working on f70-01 · 1 after it · then Claude's review", and doesn't say the second ticket waits for the lead
- a card with an escalated developer ticket and a ready lead ticket is faded and reads "developers tried f72-01 · now with the lead"
- a card with a blocked developer ticket and a ready lead ticket is faded and reads "f72-01 is blocked"
- a card holding only lead tickets still reads "lead only", and every line of `test_each_planted_card_says_what_it_holds_for_developers` still passes
- a lit card with an escalated developer ticket and no lead ticket left reads "then the lead's" that ticket, not "then Claude's review"
- the Planted stage's head counts a running ticket among the tickets developers can work on
- the legend's faded entry reads "faded: nothing for developers to take"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 4973
gate_failures: ['task-tests']
tokens: 6007023
```
