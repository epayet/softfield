---
id: f175-02-one-temp-folder-per-job
milestone: f175-if-i-leave-the-factory-running
agent: lead
difficulty: 6
depends_on: []
files:
  - runner/procs.py
  - runner/cli.py
tests:
  - tests/runner/test_procs.py
---

### Goal
Every command the runner starts gets its own temp folder, removed when its process group ends, and `softfield run` sweeps what a dead runner left, so `/tmp` stops filling between reboots.

### Context
Read D1–D3 in `.factory/cards/f175-if-i-leave-the-factory-running.md`, then `run_bounded`, `run_streaming`, `_owned`, `_kill` and `stop_all` in `runner/procs.py`, and `main` in `runner/cli.py`, where `softfield run` starts. `TOOL_DIRS` in `runner/sandbox.py` already lets a benched agent write in `/tmp`.
- The runner ends every group with SIGKILL, so nothing in it can remove its own temp files (pytest workers, Chromium profiles, Playwright): they stay in `/tmp` until a reboot, which the owner sees as 30 GB back and a slow boot.
- The folder is set as `TMPDIR` in the command's environment, over whatever `env` the caller passed (`claude_env` in `runner/claude.py`, the bench's in `runner/local_model.py`).
- Removing is `shutil.rmtree(…, ignore_errors=True)` on the folder procs made, after the group is killed, in the same `finally` that drops it from `_live`; `stop_all` removes those of the groups it stops. Nothing outside `/tmp/softfield-<uid>/` is ever removed.

### Done when
- a command run through `run_bounded` or `run_streaming` sees a `TMPDIR` under `/tmp/softfield-<uid>/` that exists while it runs and is gone after it exits, times out or is stopped
- a command started with `TMPDIR` already under that root gets no new folder, and that folder is left in place when it ends (D2)
- `softfield run`, at its start, removes each folder under the root whose runner pid isn't alive and keeps the others; anything else in `/tmp` is untouched
- a file a test leaves in `tempfile.gettempdir()` (as `test_a_page_that_names_cdn_example_com_after_the_top_bar_fails` in `tests/factory_dashboard/test_app.py` does) is gone once `softfield check-all` ends
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
