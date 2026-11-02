---
id: f175-03-what-the-disk-kept
milestone: f175-if-i-leave-the-factory-running
agent: lead
difficulty: 4
depends_on: [f175-01-look-disk, f175-02-one-temp-folder-per-job]
files:
  - .softfield/cards/f175-if-i-leave-the-factory-running.md
tests:
  - tests/runner/test_look.py
commands: [uv run softfield look disk]
---

### Goal
Measure the disk again now that jobs clean up after themselves, and fix what still grows, or record that nothing does.

### Context
Read the Plan, D1–D4 and the "Measured" heading in `.softfield/cards/f175-if-i-leave-the-factory-running.md` (f175-01's numbers, from before f175-02), then run `uv run softfield look disk`.
- What f175-02 can't reach: the metrics database's `-wal`, which grows while the dashboard keeps reading; `.softfield/var/runs/`, which keeps every job's log; deleted files held open by a long-running process (the runner, the dashboard).
- A fix that changes when the runner deletes a run's logs, or anything the owner's data lives in (the metrics database, `.softfield/var/runs/`), is not made here: it goes to a draft ADR at once (`.softfield/adr/`, status Proposed), as `docs/agents/owner.md` says ("Never lose the owner's data").

### Done when
- the card doc has the new numbers, dated, beside f175-01's, and one line per place saying whether it still grows and why
- the factory's part of `/tmp` reads near 0 outside a running job; if not, the cause is found and fixed in this ticket, with a test in `tests/runner/test_look.py` or `tests/runner/test_procs.py`
- a place that still grows and is safe to bound (a `-wal` checkpointed, a cache pruned) is bounded here with its test; one that touches the owner's data is a draft ADR, named in the card doc
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
