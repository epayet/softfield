# Milestone F175: The factory cleans up its temp files, so the disk stops filling

> **State:** ready · **Priority:** 7 · **Area:** factory · **Fast lane:** yes
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
- **D4: `softfield look disk` says where the space went,** read-only, in plain lines with sizes: `/tmp` in total and the factory's part of it (the root, `pytest-of-<user>`, Chromium and Playwright folders, `tmp*.sqlite`), the bench folder, `.softfield/var/runs/`, the metrics database and its `-wal`, and deleted files still held open by the user's processes (from `/proc/<pid>/fd`), largest first with the command that holds them. Unreadable entries are skipped, never an error.

## Measured
`uv run softfield look disk` on 2026-10-30 (f175-01), a few days after the last reboot:
- `/tmp` in all: 6.0 GB, 1,149,741 files. **`pytest-of-manu` is 5.4 GB in 1,148,932 files**, nearly all of it; the 345 Chromium folders are 41 MB, the 63 `tmp*.sqlite` databases 195 MB, the Playwright folders 0.1 MB, and `softfield-1000` isn't there yet (f175-02).
- `.softfield/var/runs/` 772 MB (3,090 files); the bench folder 7 MB; the metrics database 7.8 MB with a 4.4 MB `-wal`: none of them is the lost space.
- 1,154 deleted files still held open, but the largest are 67 MB each (shared memory of desktop programs: gnome-shell, kitty, chrome, psensor…), 635 MB beyond the 20 listed: not the factory's, and small.
- So the 30 GB is most likely pytest's folders (the factory's own test runs, over a million small files), not the leftovers of killed jobs; f175-03 should look at why they grow so large and what keeps them.

## Measured again (f175-03)
`uv run softfield look disk` on 2026-10-30, after f175-02, before the fix below:
- `/tmp` 7.2 GB, 1,397,109 files. `pytest-of-manu` 6.5 GB in 1,396,205 files (was 5.4 GB, 1,148,932); `softfield-1000` 0.3 MB in 85 files (the new per-job folders, held by a job running now); Chromium 354 folders, 42.6 MB (was 345, 41 MB); `tmp*.sqlite` 63 files, 195 MB (unchanged); Playwright 0.1 MB.
- `.softfield/var/runs/` 773 MB (was 772); metrics database 7.8 MB, `-wal` 4.4 MB (unchanged); deleted files held open 1,147, all desktop programs' shared memory.
- **Cause of the million files:** each test's `git init` copies git's template, about fifteen sample hooks (`*.sample`), into every temporary repo; a run makes thousands. pytest keeps three runs, so it is bounded, but at about 1.4 M files and 6 GB it is the whole of `/tmp`'s weight, and it is rewritten each run.
- **Fix:** `tests/conftest.py` points `GIT_TEMPLATE_DIR` at an empty folder for the whole test session, so a test repo is only what the test puts in it (`test_a_test_repo_holds_no_sample_hooks` in `tests/runner/test_look.py`). Folders already on disk go at the next three runs or the next reboot.

One line per place, does it still grow?
- `/tmp` pytest folders: grew with every run until now; bounded by pytest's three runs and, after the fix, small.
- `softfield-1000` (per-job folders): no; removed when a job's group ends, swept at the next `softfield run`.
- Chromium folders: slowly (9 in a few hours), from browser tests run by pytest outside a job's `TMPDIR`; 42 MB, a reboot empties it. Not worth a gate.
- `tmp*.sqlite`: no; the count is unchanged since f175-01, so the test that made them no longer does (the 63 are old; a reboot empties them).
- `.softfield/var/runs/` (772 MB, every job's log): yes, slowly (about 0.7 MB since f175-01). It holds the owner's data and deleting logs changes what is kept, so it is not touched here: draft ADR 39 (`.softfield/adr/39-bound-the-run-logs.md`).
- Metrics database and `-wal`: no; 4.4 MB `-wal` is steady, not worth a checkpoint job.
- Deleted files held open: no; desktop programs', not the factory's.

**Review, 2026-11-03:** the sizes above are the files' length, as `look disk` then read them; it now reads what they take on the disk. The earlier figures for small files, `pytest-of-manu` above all, are therefore lower than the space they took.
