# Milestone F250: Tell the phone when the factory is done for the week, so you can switch off

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-14.

## Notes
I want a notification when the factory is completely done for the week. No more tokens and no more dev work available. That means I can shut down my computer

## What happens today (from the code and the database, 2026-11-16)
- **Last weekend, as it happened:** Claude's week limit refused a job on Sat 14 Nov at 10:33 (`usage_events`, `seven_day`, resets Mon 16 Nov 16:00). The developer finished its last ticket at 12:40; then nothing ran in any project for about 51 hours, until the reset. Nothing told the owner.
- **What the runner knows when it has nothing to run:** each project's idle line (`_idle_line` in `runner/loop.py`, F101 D2) already names the tickets parked for Claude with their reset, the lead tickets Claude's windows pass over and until about when (`_lead_tickets_passed_over`), the tickets behind a blocked one or a sign-off, and the open owner items. `softfield run` (`run_projects`) goes round every project and waits one poll when no job ran anywhere: that round is the one place that sees the whole factory.
- **What notifies today:** the phone (ntfy, ADR 31) for what needs the owner, and soon a quiet one when Claude's limit pauses a job (F241, "A phone notification when Claude's limit pauses work", ticket f241-01 ready). The browser shows "All work done" per project when its queue empties (`notify.js`), only while a dashboard page is open.
- **Developer tickets wait on lead tickets:** in a weekend like the last one, the developer's tickets that remain mostly `depends_on` a lead ticket, so "no more dev work" follows from "no more Claude" a few hours later, not at once. That gap is why F241's notification at the refusal is not the moment to switch off.

## Expected outcome
- When no project can start anything on its own for 12 hours or more, the phone shows one notification: "Softfield · Done until Mon 16:00 (51 h): Claude's week is used up. You can switch off." When there is no work at all: "Softfield · All work done: nothing is ready. You can switch off." When something waits for the owner, the body adds "· 3 things wait for you", so they can answer before switching off. A tap opens the Overview.
- One notification per stretch of rest, not one per poll, per project or per reset.

## Done when
- f250-01 and f250-02 merged.
- To test: `softfield notify test` works on the phone. The next time Claude's week runs out (or the queue empties), about 10 minutes after the last job ends, one notification comes with the day, time and hours. Turn the computer on before that time and start the runner (or let the user units start it, if `softfield service install` was enabled): it goes on by itself at the reset.

## Decisions
- **D1: ⚑ "done" is what the whole factory can't do on its own, not one project's.** It is decided in `run_projects`' round (one runner serves every project): a round where no job ran anywhere, the owner's pause is off, and every project's remaining work is either held by Claude until a moment 12 hours or more away, or waits for the owner, or there is none. At least one of: some work is held by Claude that long, or there is no ready ticket and no queued job in any project. Work that waits only for the owner (a sign-off, a reply) never triggers it alone: their own notifications already said so. A 5-hour window rests 5 hours at most, so 12 hours means the week (its limit, or the lead tickets its reserve passes over, ADR 44 item 6).
- **D2: the time is when the first held work could start again,** the earliest of every project's Claude resumes: the parked tickets' resets (`_resets`) and the time `_lead_tickets_passed_over` gives. One function per session gives it (`claude_resumes`, new in `runner/loop.py`) and `_idle_line` uses it too, so the idle line and the notification never disagree.
- **D3: the words** (`notify.done_message`, new in `runner/notify.py`). Title "Softfield" (the factory, not a project). Body: "Done until Mon 16:00 (51 h): Claude's week is used up. You can switch off."; with no work at all, "All work done: nothing is ready. You can switch off."; either followed by " · N things wait for you" (one thing: "1 thing waits for you") when owner items are open in any project. The time and the bracket are F241 D2's (its function, f241-01): weekday in front when not today, whole hours, minutes under an hour. When it is the reserve that holds lead work rather than the limit, "Claude's week is used up" reads "Claude's week is down to your reserve", since turning the reserve switch on would give more. A tap opens the Overview. Default priority, not quiet: switching off is something to do.
- **D4: once per rest, nothing stored.** The state must hold 10 minutes (whole polls) before it sends, so a job starting a minute later stops it. Then it sends once, kept in memory; any job running re-arms it. A runner started while the factory is still done sends it again after its 10 minutes: true, and nothing is kept about the sending (ADR 31 item 4).
- **D5: one "all done" on the phone, not two.** The browser's per-project "All work done" (`notify.js`) goes: the runner's covers the whole factory and reaches a closed phone. `data-all-done` on `#live-facts` stays only if another reader needs it; f250-02 checks.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | factory-done-notifies | L | 3 | f241-01 | D1–D4: `claude_resumes`, the check in `run_projects`, `notify.done_message` |
| 02 | browser-all-done-goes | D | 2 | 01 | D5: `notify.js` loses its own "All work done" |

01 is the lead's: `runner/` is protected. 01 waits for f241-01, whose time words it reuses.

No mock-up: no dashboard page changes; D3 is the notification's words.

## Not in this milestone
- **Waking the computer by itself at the reset** (`rtcwake`, or a suspend rather than a shutdown): it changes the machine's own settings, so it needs the owner's OK and starts as a card of its own if wanted.
