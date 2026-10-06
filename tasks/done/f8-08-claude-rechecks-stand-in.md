---
id: f8-08-claude-rechecks-stand-in
milestone: f8-one-queue
depends_on: [f8-03-support-jobs-queued]
agent: lead
difficulty: 6
files:
  - runner/loop.py
  - runner/state.py
tests:
  - tests/runner/test_loop.py
---

### Goal
Every merge reviewed only by a stand-in checkpoint is checked again by Claude: one queued `checkpoint` job holds them all, and runs when Claude's window allows.

### Context
Read `stand_in_checkpoint` and `checkpoint` in `runner/loop.py` (the stand-in empties `s.state.unchecked`, so today nobody re-checks those merges), `State` in `runner/state.py`, and `queue_job` and `open_jobs` in `runner/metrics.py` with f8-03's triggers. Test-first.
- The owner (2026-10-06): while Claude is out, the factory should go on as far as it safely can. So no cap on merges: the catch-up comes after.
- A stand-in's merges join one open re-check (one queued job, its reason naming them), not one job each; a later stand-in adds to it.
- The re-check is Claude's checkpoint over those merges, with fix tickets as today. It must not run on the stand-in again.
- Its findings rate the authors as a checkpoint's do; a finding the stand-in already filed (same file and ticket) isn't filed twice.

### Done when
- two stand-in checkpoints, then Claude free: one Claude checkpoint over all their merges, and the queue empties
- while Claude is out the re-check stays queued and developer tickets still run
- `uv run runner check-all --task f8-08-claude-rechecks-stand-in` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
