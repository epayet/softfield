# Review: F290, Split runner/loop.py into one module per job kind, with no change in behaviour

**Status:** review done after round 2; ready for your sign-off.

### 1. What changed
- `runner/loop.py` went from 6,813 lines to 1,487 and now only schedules. Each job kind has its own module: `developer_job`, `lead_job`, `review_job`, `planner_job`, plus `rating_store`, `waits` and `session` under them.
- The tests moved with the code into one test file per module. All 94 tests that moved kept their names. The only test edits are imports and patch targets.
- The runner behaves the same: same jobs, prompts and pages. `AGENTS.md` item 5 now says a new job kind gets its own `runner/<kind>_job.py`.

### 2. How to test it yourself
1. Let the runner take its next ready ticket. It should pick, run, gate and merge as before.
2. Open the Overview and Line pages. The Claude meters, reserve switches and "A check fails on main" read as before (they now read from `session`, `waits` and `developer_job`).
3. Open a runner ticket in `.softfield/tasks/ready/` that names a moved function. Its `files:` point at the new module.

### 3. Done when, as of now
- **Met:** `runner/loop.py` is the scheduler only, at 1,487 lines (under 2,000).
- **Met:** no new module is over 1,800 lines (`runner/session.py` is the biggest, at 1,777), and no new test file is over 3,000 (`tests/runner/test_session.py` is the biggest, at 758).
- **Met:** move only. 94 test definitions left their files and 94 arrived. ruff and mypy are clean, and every patch left on `loop` names something the scheduler calls.
- **Met:** imports run one way. An upward import sits inside its function, with the `# runner.x imports this module` comment.
- **Met:** D6's "fixtures used by more than one file go to `conftest.py`". f290-09 moved the two autouse guards there. The review deleted the copies f290-09 left in `tests/runner/test_loop.py`.

### 5. Decisions made along the way
- **The reserve switches stayed in `runner/session.py`, not `runner/waits.py` as D1 listed.** `runner/requests.py` and the dashboard read them, and nothing about them waits. *Lead, f290-01.*
- **Helpers two jobs share stay in the first job module that has them, not in `session`** (`block`, `_check_all`, `waiting_behind`…). `block` rates the ticket, and the rating store sits above `session`. *Lead, f290-03 (replan).*
- **`runner/setup.py` imports `runner.planner` at the top instead of inside two functions.** Once the planner job left the loop there was no cycle left to dodge, so this is the one edit beyond moving code. *Lead, f290-08.*

### 6. What next
- **Factory:**
  > Add a check that fails when a module in runner/ passes 1,800 lines, or imports a module above it outside a function, so runner/loop.py can't grow back into one file.
  > Simpler: tests/runner/test_backup.py keeps its own `fake_clock` fixture and `THURSDAY` constant, which repeat the ones now in tests/runner/conftest.py; drop them for the shared ones (about 12 lines).

### 8. How the work went
- The F143 pattern (one lead "own module" ticket per move, using `cp` and `sed -i`, run in a chain) carried over to the runner: eight tickets, every one merged at its first attempt, the last seven at $0.62–$4.01 each.
- The replan after the first two moves (f290-03, $0.93) corrected five of the later tickets before they ran, and none of those five failed. Keep a replan ticket after the base of any chain of moves.
- The local model did the fixture move (f290-09) in one attempt, but it kept the originals in `test_loop.py`, so its "defined once" Done when wasn't met. The gates can't catch a duplicate fixture. For a move ticket, a Done when the tests can check (for example, "`grep` finds one definition") is worth writing.
- f290-01 cost $10.76 for 9 minutes because it resumed a session parked at a Claude limit, after 100 steps and 20M cached tokens. A large lead job may be cheaper started fresh than resumed.

### 9. What clogged the factory line
- 23:32–01:24: f290-01 waited about 1 h 50 min for Claude's limit. Meanwhile the local model spent the whole wait on f124-04: a 76-minute timeout, then a stop for no edit in 20 minutes. Nothing merged in those hours.
