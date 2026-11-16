---
id: f243-01-latest-lane-pull-wins
milestone: f243-i-can-t-undo-a-fast
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
When the owner pulls a fast lane or "use reserve" lever and pulls it back before the runner takes it, the runner applies only the latest pull: the card or switch stays as it was, and nothing is committed.

### Context
Read D1 in `.softfield/cards/f243-i-can-t-undo-a-fast.md`. In `runner/requests.py`, read `apply_requests` (how an older open `REORDER` finishes as `REPLACED`, F15 D4), `take_switches`, `_reserve`, `_card_reserve` and `_switch`. Follow the existing reserve tests in `tests/runner/test_requests.py`. `runner/**` is protected: tests first.

### Done when
- with two open `reserve` requests on the same card, `on` then `off`, on a card not marked, `apply_requests` finishes the first as `REPLACED` and the second as "taken back: F… stays out of the fast lane"; the card's doc is unchanged and no commit is made
- the mirror case (a marked card, `off` then `on`) finishes "taken back: F… stays in the fast lane", with no commit
- the same for a switch (`week` or `five_hour`), in `apply_requests` and in `take_switches`: the switch's state is unchanged and the result says it was taken back
- a single open request, or a latest one that changes the state, is applied as today; requests on other subjects are untouched
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
