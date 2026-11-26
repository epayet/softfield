---
id: f305-01-measure-what-is-written
milestone: f305-i-am-a-bit-concerned-looking
agent: lead
difficulty: 4
depends_on: []
files:
  - runner/look.py
  - runner/checks.py
  - .softfield/cards/f305-i-am-a-bit-concerned-looking.md
tests:
  - tests/runner/test_look.py
commands: [uv run softfield look disk]
---

### Goal
The factory says how much it writes to the disk: `softfield look disk` shows the writes since boot, and `softfield check-all` says what it wrote while it ran.

### Context
Read the Plan and D1, D2 and D4 in `.softfield/cards/f305-i-am-a-bit-concerned-looking.md`, then `disk` and `_size` in `runner/look.py` (F175's `look disk`) and `check_all` in `runner/checks.py`.
- The owner's system monitor shows terabytes written; free space is fine (F175), so what matters is bytes written, which `/proc/diskstats` counts per device since boot (field 10, sectors written, 512 bytes each).
- Whole disks only: skip partitions (a device with a `partition` file under `/sys/class/block/<name>/`), `loop*`, `ram*`, `zram*` and `dm-*`. An unreadable `/proc/diskstats` gives no line, never an error (as `look disk` does for unreadable entries).

### Done when
- `softfield look disk` ends with one line per whole disk: its name, GB written since boot, the hours since boot (`/proc/uptime`) and GB a day
- `softfield check-all` prints, as its last line, "wrote N GB to disk while it ran (the whole machine's writes)", N the sum over whole disks of the counter's change between its start and its end
- tests feed a sample `/proc/diskstats` and `/proc/uptime` (paths passed in, not the real ones) and check the partitions and loop devices are left out and the figures are right
- the card doc gets a dated "Measured" section with `look disk`'s new lines and one `check-all`'s figure from this ticket's own gate
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
