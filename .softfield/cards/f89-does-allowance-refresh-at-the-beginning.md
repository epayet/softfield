# Milestone F89: Claude's meters: a fresh reading before each job, and the time of the reading

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
does allowance refresh at the beginning and end of each planner task?

The owner, 2026-10-23: "Or perhaps even when I refresh the page?"

From the code (2026-10-27):
- Claude's windows are only known from a Claude job's own stream (`rate_limit_event`, `_readings` in `runner/claude.py`); there is no free way to ask. Every Claude job, planner replies included, saves what its stream read when it ends (`_record_readings` in `runner/loop.py`, called from `call_claude`). So the meters move after each reply, not before.
- Before a job, `fresh_reading` (`runner/loop.py`, f4-07) runs a Haiku probe ($0.006, 3 s on average over 113 probes) when the latest reading is over 10 minutes old, but only when a lead ticket, checkpoint, escalation or direction waits (`lead_work_ready`, which leaves planner rows out), and at most once per runner session (`Session.probed`). A runner session lasts hours, so in practice a planner reply starts on the last job's reading.
- A page refresh reads the database only (`agent_allowances` in `factory_dashboard/overview.py`): it shows the latest stored reading and never asks Claude. A reading whose reset has passed already shows "reset since, no new reading" instead of a stale percent.

## Expected outcome
Claude's meters are never silently old: the runner reads the windows before any Claude job, a planner reply included, whenever the last reading is over 10 minutes old, and every meter says when it was read.

## Done when
- A planner reply waiting with a reading over 10 minutes old gets a fresh probe first; a second job an hour later in the same runner session gets one too.
- No probe runs when the reading is under 10 minutes old, or when no Claude work waits.
- The planning room's lead window says "read at 03:59" (or "read on Oct 26 22:10" for another day) on its header; each row of the Overview's allowance says the same on its small line.

## Decisions
- **D1 No probe on a page refresh.** The dashboard stays read-only and never runs `claude -p`: a probe per refresh would run from the web server beside the runner on the same login, and the owner refreshes from a phone often. The runner's probe, every 10 minutes while Claude work waits, plus the stamp, answers "is this number fresh?".
- **D2 The probe's rule.** `fresh_reading` keeps its 10-minute staleness test and drops its once-per-session limit (`Session.probed`); planner rows count as Claude work for it. Worst case while lead work waits but is held: six probes an hour, about $0.04.
- **D3 The stamp's words.** `WindowAllowance.read_label`, from the reading row's `at`, in the same shape as `_reset_label`: "read at HH:MM" today, "read on <Mon> <d> HH:MM" otherwise; None with no reading. Picture: [`.softfield/cards/f89-mockup/lead-window.html`](f89-mockup/lead-window.html).
- **D4 After F32.** The stamp goes in the same tile as F32's reset words (`f32-01-lead-window-resets`), so its ticket waits for that one.

## Tickets
1. `f89-01-probe-before-planner` (lead): the probe runs before any Claude job, planner replies included, every time the reading is over 10 minutes old.
2. `f89-02-meters-say-when-read` (developer): the lead's window and the Overview's allowance say when Claude's windows were read.
