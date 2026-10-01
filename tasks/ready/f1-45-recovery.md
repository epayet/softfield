---
id: f1-45-recovery
milestone: f1
depends_on: [f1-44-claude-readings]
agent: lead
difficulty: 6
files:
  - runner/state.py
  - runner/loop.py
  - runner/milestone.py
  - runner/metrics.py
tests:
  - tests/runner/test_state.py
  - tests/runner/test_loop.py
---

### Goal
After a Ctrl-C, a crash or a reboot, `uv run runner milestone <key>` picks up the job that was cut off instead of refusing to start.

### Context
Read `docs/adr/15-allowance-aware-routing.md` item 11, `runner/state.py` (`State`, `save_state`), and in `runner/loop.py` `open_session` (it refuses unless main is clean), `call_claude`, `run_task` and `run_lead_task`. Test-first.
- **What happened (2026-10-01):** the owner stopped a headless review with Ctrl-C. It left 3 changed files on main, its job row `running`, and its run without an end. The next run would have refused to start. The lead tidied it by hand.
- **In-flight record:** before a job starts, `State` gets an `in_flight` entry: kind, ticket (or none), branch, agent, the job's row id, the Claude session id once known, and when it started. It is cleared when the job ends, whatever the outcome.
- **On start, with an `in_flight` entry:**
  - **A Claude job:**
    - commit the tree to its branch, or to `interrupted/<kind>-<ticket or milestone>` when it ran on main
    - go back to a clean main
    - leave the session id in state.json, so the job's next run resumes it (`call_claude`'s resume path)
  - **A local attempt:**
    - commit its wip to its task branch, as `run_task` does
    - count the attempt as timed out
  - **Either way:**
    - the job row ends with outcome `failed` and the note "interrupted"
    - the run row gets an end and the verdict "interrupted"
    - one console line says what was recovered
- **Without an entry,** a dirty tree is still refused, as today: it isn't the runner's.

### Done when
- a fake Claude job interrupted mid-way (an exception raised from the fake) leaves an `in_flight` entry; the next session commits its changes to a branch, starts on a clean main, and resumes the same session id
- an interrupted local attempt counts as a timed-out attempt on the next run
- a dirty tree with no `in_flight` entry is still refused
- `uv run runner check-all --task f1-45-recovery` passes
