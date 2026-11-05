---
id: f38-03-fake-clock-ignores-subprocess
milestone: f38-the-refresh-prompt-causes-layout-shifting
difficulty: 2
depends_on: []
tests_only: true
files:
  - tests/runner/test_loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
The `fake_clock` fixture in `tests/runner/test_loop.py` moves only when the runner itself sleeps, so a test that checks the clock stood still can't fail by 1 ms on a busy machine.

### Context
Read `def fake_clock` in `tests/runner/test_loop.py` and `.softfield/cards/f38-the-refresh-prompt-causes-layout-shifting.md` (D5).
- The cause: the fixture replaces `time.sleep` for the whole process. Python's `subprocess` calls `time.sleep` too, with a first delay of 1 ms, while it waits with a timeout for a program that hasn't ended yet. Under load that moves the fake clock, and `fake_clock[0] == THURSDAY` then fails with 12:00:00.001 (`test_the_5_hour_switch_turned_on_while_the_review_is_parked_makes_it_the_next_pick`, and `test_with_the_week_switch_off_a_lead_ticket_at_the_reserve_parks_for_the_owner`).
- The fix is in the fixture, not in the seven assertions: keep the fake sleep for the runner, and give `subprocess` the real one with a second `monkeypatch.setattr` on `subprocess`'s `time` attribute (a `types.SimpleNamespace(sleep=<the real time.sleep, saved before the patch>)`). The module uses nothing else from `time`. The `slept` list then holds only the runner's own sleeps.
- Change no assertion and no other test.

### Done when
- a new test using `fake_clock` runs `subprocess.run(["sleep", "0.05"], timeout=5)` and finds `fake_clock[0] == THURSDAY`; it fails without the fix
- every test in `tests/runner/test_loop.py` still passes, with its assertions unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1789
gate_failures: []
tokens: 1784168
```
