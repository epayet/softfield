# Milestone F305: Find what writes terabytes to the SSD, and keep test temp files in memory

> **State:** ready · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-25.

## Notes
I am a bit concerned looking at system monitoring that I'm writing terabytes of data to my disk probably from factory stuff. is it concerning for my ssd and is it needed

## Plan (lead, 2026-11-26)
- **Space is fine, writes are the question.** `softfield look disk` today: `/tmp` 19.8 MB, the factory's temp folders 0.5 MB, run logs 1.5 GB, metrics database 13.9 MB with a 4.3 MB `-wal`: F175's clean-up holds. But space left on the disk says nothing about how much was written and deleted again, which is what wears an SSD. The factory can't measure that yet: the planner can't read `/proc/diskstats`.
- **The likely writer is the factory's test runs.** The line ran 20 to 24 hours a day on most days since 2026-11-12 (`jobs`: 65 to 116 jobs a day), and every check, the gate's and each developer's own, runs the whole suite, which makes thousands of small git repos, SQLite files and Chromium profiles in the job's temp folder, then removes them. Before F175's fix the suite left about 2 GB per run; on Ubuntu `/tmp` is on the SSD, so each of those files is written (and journaled) even though it lives only minutes. Other writers to check: Docker rebuilding a project's app each time main moves (`follow_main` in `runner/stacks.py`), the review's pictures (a new worktree and `.venv` each time, `runner/shots.py`), swap.
- **Is it worrying:** a consumer 1 TB SSD is usually guaranteed for about 600 TB written (it varies from about 150 to over 1,000 by model). A few TB in total is under 1% of that; a few TB a week would use a 600 TB drive up in a few years. The drive's own counters ("Percentage used", "Data units written") settle it.
- Tickets: `f305-01-measure-what-is-written` (lead, runner), `f305-02-temp-files-in-memory` (lead, runner, after 01: measures, then moves the temp folders to memory if the tests are the writer).
- No mock-up: nothing on a page changes.

## Measured (lead, 2026-11-26, f305-01)
- `softfield look disk`'s new lines, 61 hours after boot:
  ```
  sda written since boot           1450.3 GB in 61.0 hours, 570.7 GB a day
  sr0 written since boot           0.0 GB in 61.0 hours, 0.0 GB a day
  sdb written since boot           2.7 GB in 61.0 hours, 1.1 GB a day
  sdc written since boot           0.0 GB in 61.0 hours, 0.0 GB a day
  ```
- **One `check-all`, this ticket's own gate: 7.4 GB** (`sda` 1450.3 → 1457.7 GB in about 6 minutes). Read from `look disk` before and after: the gate ran with `live`'s code, which prints the new "wrote N GB" line only once this ticket is on main. During the run the factory's temp folder held 974 MB in 67,473 files.
- **What it means:** about 570 GB a day is roughly 200 TB a year, a third of a typical 1 TB drive's 600 TB rating each year. At 7.4 GB a check and 65 to 116 jobs a day, each running one or more checks, the checks alone come to several hundred GB a day: they are the main writer, so f305-02 goes ahead with D3 (temp files in memory).

## Decisions
- **D1: writes are read from `/proc/diskstats`,** whole disks only (not partitions, loop or RAM devices), sectors written × 512. No new table, no new setting: one helper in `runner/look.py` beside `disk`. It builds on F175's `look disk` (D4) and makes nothing removable.
- **D2: `softfield look disk` adds "written since boot"** per disk: GB, the hours since boot (`/proc/uptime`) and GB a day. **`softfield check-all` ends with one line**, "wrote N GB to disk while it ran (the whole machine's writes)"; the gate's and the developers' checks are logged, so the job logs carry it. Whole-machine figures, not per process: simple, and the line is the machine's main writer when it runs.
- **D3: the factory's temp root moves to `/dev/shm/softfield-<uid>/`** (memory) when `/dev/shm` is a tmpfs with at least 4 GB free, else it stays `/tmp/softfield-<uid>/`. Same checks as today in `_tmp_root` (`runner/procs.py`: our own folder, mode 0700, no link), same removal per job and sweep at `softfield run` (F175 D1–D3). The bench's sandbox already may (`TOOL_DIRS` in `runner/sandbox.py` holds `/dev`, for Chromium), so the sandbox doesn't change. Made only if 01's numbers show the check runs are most of the writes; otherwise 02 records what is and drafts its fix.
- **D4: nothing the owner keeps moves to memory:** run logs, the metrics database, the bench folder and the review's pictures stay on the disk.
