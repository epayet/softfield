---
id: f1-46-parking-and-reserve
milestone: f1
depends_on: [f1-45-recovery]
agent: lead
difficulty: 7
files:
  - runner/loop.py
  - runner/state.py
  - runner/cli.py
  - runner/milestone.py
  - runner/owner.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_cli.py
  - tests/runner/test_owner.py
---

### Goal
While Claude is limited or down to its reserve, the queue keeps the GPU busy with work that doesn't need Claude, and it asks the owner before lead work spends the reserve.

### Context
Read `docs/adr/15-allowance-aware-routing.md` items 4, 5 and 10, `runner/allowance.py` (f1-43), and in `runner/loop.py` `call_claude` (today it sleeps through a limit, and the GPU idles), `work_queue` and `pick_next` (`runner/tasks.py`). Test-first.
- **Parking:**
  - A Claude job stopped by a limit commits its wip to its branch and records itself in `State` (kind, ticket, branch, session id, reset). It doesn't sleep.
  - `work_queue` then picks only work that needs no Claude: developer tickets whose agent is local. A developer ticket that would need a direction waits parked too, rather than going undirected.
  - When the earliest reset has passed, parked jobs resume first (`--resume` with their session id).
  - When nothing runnable is left, the runner sleeps until the earliest reset, as today.
- **The reserve (items 4–5):** before a lead ticket starts, the loop asks `runner/allowance.py` with Claude's latest readings (f1-44's `usage_events`).
  - **Refused only because of the reserve:** the console asks `Claude is at its reserve (N% of the week left, resets <day time>). Use it for the rest of this run? [y/N]` and waits 10 minutes on stdin. With no answer, or no terminal, it parks the ticket and adds an owner item (`owner_items`, kind `reserve`, with the command to rerun).
  - **A yes lasts for the running command only** (the owner, 2026-10-01). It is kept in memory, not in `State`. It survives the self-restart in `runner/cli.py` (`os.execv` after a runner change), for example through an environment variable that only that restart sets. A fresh `runner milestone` after a Ctrl-C asks again if the allowance is still low.
  - Support roles (reviews, escalations, directions, checkpoints) may always use the reserve.

### Done when
- a fake limit on a lead ticket parks it, the next local developer ticket runs, and the parked job resumes its session after the (injected) reset
- with a reading of 0.79 of the week used on a Thursday, a lead ticket asks; "y" runs it, and no answer parks it and writes the owner item
- after a yes, a second lead ticket in the same run doesn't ask; after the self-restart it still doesn't; a new process asks again
- `uv run runner check-all --task f1-46-parking-and-reserve` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
