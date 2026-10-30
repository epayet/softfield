---
id: f175-01-look-disk
milestone: f175-if-i-leave-the-factory-running
agent: lead
difficulty: 4
depends_on: []
files:
  - runner/look.py
  - runner/cli.py
  - .factory/cards/f175-if-i-leave-the-factory-running.md
tests:
  - tests/runner/test_look.py
commands: [uv run softfield look disk]
---

### Goal
`softfield look disk` says, read-only, where the factory's disk space went, so the owner's lost 30 GB can be traced and the fix measured.

### Context
Read D4 in `.factory/cards/f175-if-i-leave-the-factory-running.md`, then `sql` and `page` in `runner/look.py` and the `look` subcommand in `runner/cli.py`; `bench_dir` in `runner/bench.py` gives the bench folder and `cfg.metrics_db` the database.
- The owner got 30 GB back at their last reboot, and the boot was slow. The planner listed about 117,000 files in `/tmp` days after it, but couldn't size them; the Plan in the card doc says what it saw.
- Sizes are walked with `os.scandir`, not `du`, without following links; an entry that can't be read is skipped. Deleted-but-open files are the `/proc/<pid>/fd/*` links ending in ` (deleted)` among the user's processes, sized by `os.stat` on the link.

### Done when
- `softfield look disk` prints one line per place in D4, its size in MB or GB and its file count, the factory's parts of `/tmp` each on their own line, and the deleted-but-open files largest first with the pid and command holding them
- a folder that doesn't exist reads as 0, and an unreadable entry is skipped without an error
- it writes nothing anywhere
- at the end, run `uv run softfield look disk` on the branch and add what it printed, dated, under a "Measured" heading in the card doc
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
