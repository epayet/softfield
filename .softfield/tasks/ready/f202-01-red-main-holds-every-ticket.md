---
id: f202-01-red-main-holds-every-ticket
milestone: f202-while-main-is-red-hold-tickets
agent: lead
difficulty: 4
depends_on: []
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
While main fails its tests, the runner starts no ticket but the one that would mend main, and a red main's failing checks add up instead of replacing each other.

### Context
Read D1, D2 and D5 in `.softfield/cards/f202-while-main-is-red-hold-tickets.md` and ADR 47 in `.softfield/adr/47-a-red-main-holds-every-ticket-but-the-mender.md`, then `red_main_text`, `_main_is_red`, `_waits_for_red_main`, `waits_for_main` and `_held_by_red_main` in `runner/loop.py`. Follow the red-main tests in `tests/runner/test_loop.py` (search `main_red`). `runner/**` is protected: tests first.
- `MAIN_TESTS` ("tests") is check-all's name for the test suite; a developer's wait writes it as the failing check.
- `_main_is_red` today overwrites `s.state.main_red` whole; with it already set, keep `head`, `ticket` and `mender` and only add the new check names.

### Done when
- with `main_red["checks"]` holding `tests`, `waits_for_main` returns every ready ticket's id but the mender's, developer tickets included
- with `main_red["checks"]` `["layout"]` only, a developer ticket not in `waits_on_main` is not held, as today
- a second red-main failure on `tests` while main already fails `layout` leaves `checks` as `["layout", "tests"]`, and `_look_at_main` keeps main red while `layout` still fails
- the owner's item reads "no other ticket runs until main passes" when the checks hold `tests`, "no other lead ticket" otherwise, and ends "nothing would mend it yet" with no mender
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
