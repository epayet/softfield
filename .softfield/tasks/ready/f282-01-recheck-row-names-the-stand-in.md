---
id: f282-01-recheck-row-names-the-stand-in
milestone: f282-this-was-in-the-queue-while
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/loop.py
  - runner/state.py
  - runner/instructions/author/known-range.md
tests:
  - tests/runner/test_loop.py
---

### Goal
When Copilot stands in for Claude's checkpoint, that checkpoint is final: no re-check by Claude is ever queued for its merges (ADR 53).

### Context
Read ADR 53 in `.softfield/adr/53-copilots-checkpoint-is-final.md` and D1 in `.softfield/cards/f282-this-was-in-the-queue-while.md`. Then `checkpoint_reason`, `_drop_covered_merges`, `note_merge`, `RECHECK_NOTE`, `_recheck_note`, `checkpoint` and `stand_in_checkpoint` in `runner/loop.py`, and `recheck` / `recheck_filed` in `runner/state.py`.
- Today `stand_in_checkpoint` moves its merges from `unchecked` to `recheck`, and `checkpoint` parks for Claude while `recheck` is not empty.
- The tests asserting the re-check are near lines 7110, 7207 and 7266 of `tests/runner/test_loop.py`. Rework or remove them.
- In `runner/instructions/author/known-range.md`, the "Checkpoints" bullet ends with a sentence about Copilot's review bench on F2's checkpoint 189 (2026-10-02). It is out of date (ADR 53 item 4).

### Done when
- after a stand-in checkpoint passes, its merges are neither in `unchecked` nor waiting for anything, and the checkpoint row is finished, not parked
- a stand-in that fails or can't run still leaves its merges unchecked, and the row parks for Claude as today
- `recheck`, `recheck_filed`, `RECHECK_NOTE` and `_recheck_note` are gone; a state file that still has them loads, and a checkpoint row queued only for a re-check is finished at the next pick without a job
- `checkpoint_reason` says only "after … merged"
- the known-range "Checkpoints" bullet no longer has the Copilot bench sentence
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
