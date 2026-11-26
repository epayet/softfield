---
id: f305-02-temp-files-in-memory
milestone: f305-i-am-a-bit-concerned-looking
agent: lead
difficulty: 5
depends_on: [f305-01-measure-what-is-written]
files:
  - runner/procs.py
  - runner/shots.py
  - .softfield/cards/f305-i-am-a-bit-concerned-looking.md
tests:
  - tests/runner/test_procs.py
commands: [uv run softfield look disk]
---

### Goal
If the factory's check runs are most of what it writes, their temp files live in memory instead of on the SSD; either way, the card says what writes the terabytes.

### Context
Read the Plan, D3 and D4 and the "Measured" section f305-01 wrote in `.softfield/cards/f305-i-am-a-bit-concerned-looking.md`, then `TMP_BASE`, `_tmp_root`, `_job_tmp` and the sweep at `softfield run`'s start in `runner/procs.py`, and `_worktree` in `runner/shots.py` (a worktree and a `.venv` per review, made in a temporary folder).
- First compare: the GB a day from `look disk` against the `check-all` figures in the job logs of the last day under `.softfield/var/runs/` (grep "wrote"), times the number of checks run that day. Also look for the other writers named in the Plan: Docker rebuilds (`follow_main` in `runner/stacks.py`), the review's worktrees.
- `/dev/shm` is shared like `/tmp`: `_tmp_root`'s checks (our own folder, 0700, not a link) apply there unchanged. The bench's sandbox already writes under `/dev` (`TOOL_DIRS` in `runner/sandbox.py`); leave that file as it is.
- Nothing the owner keeps moves (D4): run logs, the metrics database, the bench folder, the pictures.

### Done when
- the card doc says, dated, what share of the day's writes the checks are, and names any other large writer with its figure
- if the checks are most of it: the temp root is `/dev/shm/softfield-<uid>/` when `/dev/shm` is a tmpfs (read from `/proc/mounts`) with at least 4 GB free (`os.statvfs`), else `/tmp/softfield-<uid>/`; the sweep at `softfield run` covers whichever root is in use; `shots.py`'s worktree is made under the job's temp folder; tests cover both roots and the fallback, with the mounts file and free space passed in
- the card doc records one `check-all`'s figure after the change beside f305-01's, and the largest the job's temp folder grew during it
- if the checks are not most of it: nothing in `runner/` changes, and the card doc names the writer and the fix, drafted as a planted-card text or a ticket in `.softfield/tasks/later/`
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
