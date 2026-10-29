# Milestone F175: The factory cleans up its temp files, so the disk stops filling

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-26.

## Notes
if i leave the factory running for a long time, the disk space goes away, probably lots on the tmp folder. i can see impact when i reboot computer, it takes a long time to boot next time, probably cleaning tmp folder. when i rebooted my computer last, there was 30GB of disk space that came back. make the factory less space hungry, or better at cleaning up

## Plan (lead, 2026-10-27)
- **What /tmp holds today, a few days after the last reboot** (read by the planner, which can list files but not size them): about 117,000 files. pytest's folders (`/tmp/pytest-of-manu/pytest-37` to `-39`, a few thousand small git repos; pytest keeps the last three runs, so this part stays bounded), 25 `tmp*.sqlite` databases left by one test (`test_a_page_that_names_cdn_example_com_after_the_top_bar_fails` in `tests/factory_dashboard/test_app.py` backfills a database from this repo's runs and never removes it, one per test run), 23 Chromium temp folders left by browser tests, and small caches of node, uv and LM Studio.
- **Why things are left behind:** every job and every check runs in its own process group, and the runner ends each group with SIGKILL (`_owned` and `run_streaming` in `runner/procs.py`) so nothing outlives it (2026-10-03, 2026-10-15). A process killed that way can't remove its temp files: a pytest worker's tmp, a Chromium profile, a Playwright download. A timeout, a stuck attempt or a gate that fails fast all leave theirs in `/tmp`, and Ubuntu empties `/tmp` only at boot, which is the slow boot.
- **What isn't known yet:** what the 30 GB were. `/tmp` is the likeliest, but space also comes back at a reboot when a long-running process holds a deleted file open, or when the metrics database's write-ahead log (`factory-metrics.sqlite-wal`), which the dashboard's readers keep from shrinking, is folded back at the last close. So the plan measures first, fixes the cause it can see, then measures again.
- Tickets: `f175-01-look-disk` (lead, runner), `f175-02-one-temp-folder-per-job` (lead, runner), `f175-03-what-the-disk-kept` (lead, after 02: measures again, fixes what still grows or says it's done).
- No mock-up: nothing on a page changes.

## Decisions
- **D1: one temp folder per job, removed when its group ends.** `runner/procs.py` gives each command it starts (`run_bounded`, `run_streaming`) a fresh folder under `/tmp/softfield-<uid>/`, named `<runner pid>-<n>`, as `TMPDIR` (Python, pytest, node, Chromium, Playwright, Claude Code and OpenCode all honour it), and removes it after the group is killed, whatever ended it. The root stays in `/tmp`, so a reboot still empties it, and the bench's sandbox already lets agents write there (`TOOL_DIRS` in `runner/sandbox.py`).
- **D2: a nested command keeps its job's folder.** When `TMPDIR` is already a folder under that root (an agent's `softfield check-all` inside its job), procs gives no new one: the job's folder holds it all and goes with the job, so a screenshot a test leaves in `tmp_path` is still there for the agent to read until the job ends.
- **D3: `softfield run` sweeps leftovers at its start:** every folder under the root whose runner pid is no longer alive is removed (a runner killed by a reboot, a crash, a SIGKILL). Only folders under the root, never anything else in `/tmp`: what other programs leave there is theirs.
- **D4: `softfield look disk` says where the space went,** read-only, in plain lines with sizes: `/tmp` in total and the factory's part of it (the root, `pytest-of-<user>`, Chromium and Playwright folders, `tmp*.sqlite`), the bench folder, `.factory/var/runs/`, the metrics database and its `-wal`, and deleted files still held open by the user's processes (from `/proc/<pid>/fd`), largest first with the command that holds them. Unreadable entries are skipped, never an error.
