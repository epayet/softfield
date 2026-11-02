---
id: f136-01-gone-card-leaves-the-board
milestone: f136-if-i-forgot-about-a-projject
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/loop.py
  - runner/metrics.py
  - runner/setup.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_metrics.py
---

### Goal
A card whose doc left `.softfield/cards/` leaves the board even when another doc has the same short key, so two cards never share one thread.

### Context
Read D5 in `.softfield/cards/f136-if-i-forgot-about-a-projject.md`, then `sync_cards` in `runner/loop.py`, `remove_cards` and `_card_short` in `runner/metrics.py`, and `publish_cards` in `runner/setup.py`.
- Today `sync_cards` passes `present` as short keys, so in test-factory-hello the old `m1-hello-and-happy-birthday` row (its doc gone) stays on the board beside `m1-uv-run-hi`, and both share the `m1` thread.
- Card docs are never renamed, so a row's full key is the doc's file stem (`milestone_key(path.stem)`).
- `publish_cards` runs before the runner's first round: it removes such rows the same way.

### Done when
- with docs `m1-new.md` only, a card row `m1-old` is marked removed and `m1-new` stays
- a row whose short key no doc has is removed as today; a row whose doc is there but unreadable stays where it is, as today
- `publish_cards` removes the same rows
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
