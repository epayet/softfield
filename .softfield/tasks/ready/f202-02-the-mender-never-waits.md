---
id: f202-02-the-mender-never-waits
milestone: f202-while-main-is-red-hold-tickets
agent: lead
difficulty: 4
depends_on:
  - f202-01-red-main-holds-every-ticket
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
The ticket that would mend a red main never waits for main itself, and a repair ticket queued after main went red is found as the mender as soon as it is ready.

### Context
Read D3 and D4 in `.softfield/cards/f202-while-main-is-red-hold-tickets.md` and ADR 47 items 3 and 4, then `_mender`, `_main_is_red`, `_waits_for_red_main`, `_settle_lead_task`, the attempt loop in `run_task` (where `failed.name == ALL_TESTS`) and the pick loop that calls `_look_at_main` and `waits_for_main` in `runner/loop.py`. `runner/**` is protected: tests first.
- Today a mender that fails a check main fails waits on its branch like any other ticket, and main waits for it: nothing moves.
- `main_red` gains `said`: the failing checks' output, its first 4000 characters, written by `_main_is_red`. A state file without it still loads.

### Done when
- a lead ticket that is `main_red["mender"]` and fails a check main fails is settled as a failed attempt (blocked on its last attempt), not left waiting for main
- a developer ticket that is the mender and fails only `all-tests` counts the attempt as failed, with no wait and no `regate` entry
- with `main_red["mender"]` None, a ticket made ready whose `files:` names a path in `said` becomes the mender at the next pick, is saved in the state and is not held
- a state file whose `main_red` has no `said` loads, and its mender stays as it was
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
