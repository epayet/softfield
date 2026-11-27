# Review: F305, Find what writes terabytes to the SSD, and keep test temp files in memory

- **Status:** done, signed off by the owner on 2026-11-27.

**Status:** review done after round 1; ready for your sign-off.

### 1. What changed
- **The factory's checks no longer write to the SSD.** One check wrote 7.4 GB before. After this change, this review's own checks wrote 0.1 GB and 0.0 GB. The temp files live in memory (`/dev/shm`) now, so the roughly 570 GB a day the machine was writing should drop by most of that.
- **You can see what is written.** `softfield look disk` lists what each disk has written since boot, with a figure per day. It also shows the size of the factory's temp folder in memory. Every check's log now ends with "wrote N GB to disk while it ran".
- **The memory move is careful.** The temp folder goes to memory only when at least 4 GB is really free (the review added this check). Otherwise it stays on the disk as before.

### 2. How to test it yourself
1. In the System Monitor (or `softfield look disk`), note the "sda written since boot" figure. Check it again after a few hours of the runner working. The daily rate should fall well below 570 GB.
2. Open any ticket's job on the dashboard and read its check log. The last line says how many GB the check wrote, and should be under 1 GB.
3. Later, read the drive's own wear counter ("Percentage used" in the Disks app's SMART data) and compare it a month apart.

### 3. Done when, as of now
- **Met:** the factory can measure what is written. `look disk` gives it per disk since boot, and every `check-all` gives it for the check's own run.
- **Met:** the writer was found and named in the card. The checks wrote 3.5 to 7.4 GB each, which is 60 to 100% of the day's writes. Swap, Docker and the review's pictures were checked and are small.
- **Met:** the temp files are in memory when there is room. Measured after the runner restarted on the new code: a full check wrote 0.0 to 0.1 GB.
- **Your check:** the daily rate in the System Monitor over the next days.

### 5. Decisions made along the way
- **"4 GB free" now means free memory, not only free tmpfs room.** `/dev/shm` always reports about half the memory as free, however full the memory is. A full memory would push the temp files into swap, which is on the same SSD. The review made the free figure the smaller of the two. *The review.*
- **A command inside a job keeps its runner's temp root.** Before the review's change, a `check-all` started inside a job chose the root again on its own. If memory had dropped in between, it would make a second folder on the disk. *The review.*
- **The review's picture worktree moved to memory too, beyond D3's list.** It is rebuilt and deleted every round, like the test files. The pictures it takes still go to the disk, as D4 says. *Lead, f305-02.*

### 6. What next
- **Factory:**
  > Show "GB written to the SSD today" on the Overview page from /proc/diskstats, so I can see the wear without opening the System Monitor.
  > When the runner starts, also sweep the temp root it did not choose (/tmp/softfield-<uid> when the root is in /dev/shm, and the other way round), so leftovers from a switch don't sit there until reboot.

### 8. How the work went
- f305-02's own gate ran on the old runner, so it never ran the suite with temp files in memory. The first run on the new code failed two sandbox tests. Their fixture assumed `/dev` couldn't hold the test's folders. The review fixed both tests. Lesson: a change to where tests run needs one run on the new runner before it merges, and the card said so ("not measured yet").

### 9. What clogged the factory line
- The plan was ready at 00:52, but f305-01 started only at 11:03. The ten hours went to Claude's usage limit: the line parked the lead's work until the window reset.
