---
id: f8-04-reserve-switches
milestone: f8-one-queue
depends_on: [f8-01-work-queue-table]
agent: lead
difficulty: 5
files:
  - runner/requests.py
  - runner/loop.py
  - runner/cli.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
---

### Goal
Two switches, the week's reserve and the owner's 25% of the 5-hour window, replace the runner's y/N questions.

### Context
Read `docs/adr/22-one-visible-queue.md` item 4, D4 in `docs/milestones/f8-one-queue.md`, `runner/requests.py` (`apply_requests`), and in `runner/loop.py` `at_reserve`, `at_five_hour`, `_ask_five_hour`, `read_answer`, `ReserveAnswer` and `RESERVE`/`FIVE_HOUR`; the restart's environment hand-over in `_restart` in `runner/cli.py`. Test-first.
- Off (the default) behaves as an unanswered question does today: at the week's reserve a lead ticket waits for the owner (its Needs-you item now says which switch lets it run); at the 5-hour line it parks until the reset. On behaves as a yes.
- The switches outlive commands and restarts (`var/runs/state.json`), so the environment hand-over for the answers goes.
- **On lasts 24 hours** (owner, 2026-10-04): then it is off again and a Needs-you item `reserve` asks to turn it on again. `uv run runner run --use-reserve` turns both on for 24 hours at start; `--use-reserve week` or `--use-reserve five-hour` turns one.

### Done when
- a `reserve` request `five_hour on` lets a lead ticket run past 75% of the window, and `off` parks it; the same for `week`
- no command reads the console for a reserve answer
- `uv run runner reserve week on` records the same as the request
- a switch turned on 24 hours ago reads off, and its Needs-you item is open; `runner run --use-reserve five-hour` turns only that one on
- `uv run runner check-all --task f8-04-reserve-switches` passes
