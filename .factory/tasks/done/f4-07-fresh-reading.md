---
id: f4-07-fresh-reading
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 4
files:
  - runner/loop.py
  - runner/claude.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_claude.py
---

### Goal
When a session starts with Claude work ready, the runner takes a fresh reading of Claude's windows before deciding to park or ask, instead of trusting the last session's.

### Context
Read `runner/claude.py` (how `rate_limit_event` becomes readings), `runner/loop.py` (`open_session`, `_read_windows`, `claude_hold`, `_at_five_hour`) and `runner/metrics.py` `latest_readings`. Test-first.
- **Why:** readings are only taken while a Claude job runs. A new session reuses the last stored reading whenever its window hasn't reset, so once a run began believing it was in the owner's reserve (the owner, 2026-10-02) when the window had room.
- **Find the cheapest fresh reading:** a minimal `claude -p` call (one short prompt, no tools, Haiku or the cheapest model the Pro login allows) whose stream carries a `rate_limit_event`. Check that it does, and what it costs, with one real call. Record it like any reading, and as a job with role `probe`, so the dashboard counts it.
- Take it at most once per session, and only when the queue has Claude work (a lead ticket or parked support) and the latest reading is older than 10 minutes.

### Done when
- a session whose stored reading says 80% and whose fresh reading says 20% runs the lead ticket without parking or asking
- no probe is made when no Claude work is ready, or when the reading is under 10 minutes old
- a failed probe (no event, an error) falls back to the stored reading, with a log line
- `uv run runner check-all --task f4-07-fresh-reading` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
