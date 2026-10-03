---
id: f4-03-requeue-preflight
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 4
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
finding: f2-F4
---

### Goal
A ticket an escalation requeues is pre-flighted before the runner commits it; with problems, it goes back to the lead's job once, then blocks with the problems named.

### Context
Read `runner/loop.py` `handle_escalation` (the `outcome == "requeue"` branch), `runner/tasks.py` `preflight` and `docs/backlog.md` (`[f2-review, f2-F4]`). Test-first.
- **Why:** a requeue with bare paths has cost a whole run three times (f1-36, f1-15, f2-06). The written rule in `docs/agents/lead.md` hasn't stopped it.
- **The rule:** after the escalation's job, before the commit, run `preflight` on the requeued file in `ready/`. When it finds problems, give the same Claude session one repair turn with the problems listed. The direction repair already does this for directions (look for "repair dropped, pre-flight" in `runner/loop.py`), so follow that pattern. If problems remain, block the ticket with them as the reason, instead of letting the next run fail at pre-flight.
- Remove the f2-F4 bullet from `docs/backlog.md`.

### Done when
- a requeue whose ticket names a missing bare path gets one repair turn listing that path
- a repaired ticket is committed and runs; one still broken is blocked, with its problems in the reason
- a clean requeue is committed as today, with no extra turn
- `uv run runner check-all --task f4-03-requeue-preflight` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
