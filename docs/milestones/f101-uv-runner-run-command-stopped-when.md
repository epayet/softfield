# Milestone F101: the runner waits instead of ending when it has nothing to run

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-10.

## Notes
uv runner run command stopped when it had nothing to do because of claude on reserve rather than waiting for it to come back

(2026-10-12, terminal session) when i left the runner last week (which said had nothing to do and stopped working), it said that there were things to review and signoff and did nothing

## What happened (from the code and the session report, 2026-10-12)
- **10 Oct, 19:10:** the run lasted 2.9 minutes and ended ([report](../sessions/2026-10-10-1910.md)). All 22 runnable lead tickets waited for Claude's weekly reserve (1% of the week left), and no developer ticket could run: about 20 depended on f12-03, a lead ticket.
- **Why it ended instead of waiting:** `work_queue` in `runner/loop.py` sleeps only for a reset a parked job waits for (`_wait_for_reset`). A ticket at the weekly reserve "waits for the owner, not the week", so nothing was slept on and the run returned.
- **What ending costs:** a stopped runner applies nothing from the dashboard. The reserve switch, a plan's approval, a sign-off, a plant: each waits until someone starts the runner from a terminal. Two days passed that way (10 to 12 Oct), with the week's reset on the 12th at 17:00 going unused too.
- **What already works:** when the owner pauses the factory, the run holds and applies their requests every 5 seconds (`_hold_for_the_owner`). The same hold fits here.

## Expected outcome
`uv run runner run` ends only when the owner ends it. With nothing it can run, it stays up, says what it waits for, applies every request from the dashboard as it comes, and starts again by itself when work appears or Claude comes back.

## Done when
- With every ready ticket waiting for Claude's reserve and no developer ticket runnable: the run doesn't end. The console and the Overview's Now say "Idle: 22 tickets wait for Claude's reserve · the week resets Mon 17:00".
- Turn the reserve switch on from the dashboard: the next ticket starts within seconds, with no terminal.
- When the week resets, the next ticket starts by itself.
- With an empty queue: the run stays up ("Idle: nothing is ready"). Approving a plan from the desk queues its tickets and the first one starts.
- What waits on the owner (a sign-off, an answer, a blocked ticket) is named in the idle line, once each, not repeated every poll.
- `uv run runner run --once` and Ctrl-C end the run as today, and a session report is written.

## Decisions
- **D1 Idle is a hold, not an end.** Where `work_queue` returns today with nothing to run, it holds as it does for the owner's pause: every 5 seconds it applies the owner's requests, checks the backup and reads Claude's windows, and it picks again as soon as anything is runnable. This goes for `runner run` only: `runner milestone` still ends with its verdict.
- **D2 The idle line says why, in plain words,** from what the pick already knows: tickets parked for Claude (with the reset time), tickets waiting on a blocked one, items waiting for the owner. It is the run's activity, so Now and the phone show it.
- **D3 One session report a day while idle,** not one per wake: an idle run writes its report when it ends or at midnight, so `docs/sessions/` doesn't fill with empty reports.
- **For the owner to weigh:** a run that never ends holds the GPU's model loaded and keeps a terminal busy. The alternative, a system service that restarts the runner, needs systemd (lead.md: not without asking) and still wouldn't apply requests between runs. I recommend the hold.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | idle-holds | L | 6 | – | D1, D2, D3 (`runner/` is protected) |
