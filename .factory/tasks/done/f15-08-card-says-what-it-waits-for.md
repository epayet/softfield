---
id: f15-08-card-says-what-it-waits-for
milestone: f15-reprioritising-tickets
difficulty: 3
depends_on: [f15-02-board-shows-the-order]
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
A card on the board whose tickets can't start yet says which cards it waits for, so moving it up is not a surprise when nothing happens.

### Context
Read `.factory/cards/f15-reprioritising-tickets.md` (D6). In `factory_dashboard/board.py`: `Card`, and `_cards`, which already holds every ticket of every milestone (`t.*`, with `state` and `depends_on`). In `factory_dashboard/queries.py`: `depends_on(row)` gives a ticket row's dependencies as a tuple, and the line `waits=tuple(d for d in t.depends_on if d not in done)` is the rule to copy. In `factory_dashboard/templates/board.html`: the `card_link` macro, where `c.note` shows.
- The owner (2026-10-13): "'wait for fxx' sounds like a good mvp approach". The runner skips a ticket that waits for another whatever its card's place; the reorder is never refused.
- A new field on `Card`: `waits`, the short keys in capitals (`F22`) of the **other** cards it waits for, in key order, each once.
- A milestone's card waits when it is planted or growing, has at least one ticket in state `ready`, and **every** one of its `ready` tickets depends on a ticket that is not `done`. The cards named are those of the unfinished tickets its `ready` tickets depend on, its own left out. A ticket id's card is its part before the second `-` (`f22` of `f22-01-archive-at-the-bottom`).
- When one of its `ready` tickets can start, the card waits for nothing. When the only unfinished dependencies are its own tickets, it waits for nothing too.
- A bug's card, and a seed, sprouting, ripe or harvested card, never waits.
- On the card, one line in the look of `c.note`: "waits for F22" or "waits for F22, F63".

### Done when
- a planted card whose only ready ticket depends on F22's unfinished ticket has `waits == ["F22"]` and its card reads "waits for F22"
- with two ready tickets, one depending on F22's unfinished ticket and one free, `waits` is empty and the card shows no such line
- with ready tickets depending on unfinished tickets of F22 and F63, the line reads "waits for F22, F63", each once
- a dependency that is done, and one on the card's own earlier ticket, name no card
- a bug card and a ripe card have no such line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 7069
gate_failures: ['ruff']
tokens: 8574093
```
