# Milestone F241: A phone notification when Claude's limit pauses work, saying when it resumes

> **State:** ready · **Priority:** 5 · **Area:** factory
> Planted by the owner on 2026-11-11.

## Notes
I want a notification when a job has to pause due to Claude lead limit and it should say when it can resume with how many hours in brackets

## What happens today (from the code and the database, 2026-11-11)
- **A Claude limit pauses a job silently.** When Claude refuses a job for a usage limit (`result.refusal` in the job loop of `runner/loop.py`, around "a limit (ADR 15 item 12)"), the runner records the refusal (`usage_events`, kind `refusal`, with its `resets_at`), then parks the job (`_park`) or waits in place. Only the console and the run's report say so. Nothing reaches the phone or the desk.
- **What already notifies about Claude:** an expired login (`claude-login`), and a lead ticket parked for the owner's 25% of the 5-hour window ("Claude's reserve: your choice", which asks for the switch). Both ask something of the owner; a limit asks nothing.
- **How often:** 11 Claude refusals from 2026-11-02 to 2026-11-10, two of them the week's limit (waits of 3 days or more). Several jobs refused for the same reset come within minutes of each other (2026-10-22: three in 3 minutes; 2026-10-27: Opus and Sonnet 16 s apart).
- **The phone's words are kinds, never a card's title** (ADR 31 item 1): a reset time is fine to send.

## Expected outcome
- When Claude's limit pauses the factory's work, the phone shows one notification: "softfield · Claude's 5-hour limit: work waits until 22:30 (3 h)", or for the week's limit "… until Mon 16:00 (77 h)". A tap opens the Overview.
- Several jobs refused for the same reset are one notification.

## Done when
- f241-01 merged.
- To test: `softfield notify test` works on the phone; the next time Claude's limit pauses a job (about once a day lately), one notification comes with the time and the hours. The run's report keeps its "Paused …" or "Parked …" line as today.

## Decisions
- **D1: ⚑ the first notification that needs nothing from the owner.** F114 D4 and ADR 31 item 7 kept notifications to what needs the owner; this card adds one kind that only informs, at the owner's word. It goes to the phone through ntfy only: no owner item, so nothing on the desk ("Needs you" stays for what does) and nothing in the browser.
- **D2: the words.** Title the project, as every ntfy notification. Body: "Claude's 5-hour limit: work waits until HH:MM (N h)"; "Claude's week limit" for `seven_day`; "Claude's limit" for any other window or none. The time is the machine's local time, with the weekday in front ("Mon 16:00") when it isn't today. The brackets: whole hours, rounded to the nearest, "(N h)"; under an hour, minutes, "(40 min)". With no reset known, the time is when the runner tries again. A tap opens the Overview.
- **D3: one per reset, with nothing new stored.** Before the refusal is recorded, the runner reads Claude's earlier refusals (`metrics.refusals(conn, "claude")`): when one recorded in the last 6 hours has a `resets_at` within 10 minutes of this one (both empty counts as the same), it sends nothing. One runner serves every project, so this holds across projects too.
- **D4: only a certain Claude limit.** A refusal that only looks like a limit (`limit.certain` false) retries within minutes and doesn't notify; an expired login keeps its own item; other harnesses (Copilot, the local model) don't notify.
- **D5: quiet.** Sent with ntfy's low priority (header `Priority: low`): it shows in the phone's list without a sound or a vibration, since there is nothing to do. The others keep the default.
- **D6: no "resumed" notification.** The work goes on by itself at the reset.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | limit-pause-notifies | L | 2 | – | D1–D5: the words in `runner/notify.py`, the send and the one-per-reset check in the job loop |

The lead's: `runner/` is protected.

No mock-up: no dashboard page changes, only a phone notification; D2 is its words.
