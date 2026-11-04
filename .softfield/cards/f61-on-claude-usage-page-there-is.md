# Milestone F61: Claude's meters say when the window runs out at this rate

> **State:** ready · **Priority:** 5 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
as nice to have, could do the smae here

The owner on the thread (2026-10-26), quoting Claude's own usage page: "at this rate you'll be out by Friday afternoon".

## Why
Last week's Claude week ran out on Thursday 23 Oct at 19:38 and came back on Monday 26 Oct at 17:00: almost three days with no Claude. The meter said 58% on Wednesday at 22:44 and green, under its mark. At that rate it would be out on Thursday about 13:40, so a line saying so would have warned a day and a half ahead.

The pace line (f9-29) holds back only lead tickets. Planner jobs ran on the reserve (ADR 20 item 2) and cost $150 of the week's $305 of Claude jobs, so pacing alone didn't stop the week from running out.

## Decisions
- **D1 What it says:** under each of Claude's two meters (the 5-hour window and the week), one line:
  - "at this rate: out Thu 13:38, 3 days 3 h before the reset", in the warn ink, when the window would run out before its reset;
  - "at this rate: lasts to the reset, about 79% by then", in the muted ink, when it wouldn't.
  - The time is the time alone when it is less than 24 hours away, else the short weekday and the time ("Thu 13:38"). The gap is rounded to whole days and hours, or to minutes when under an hour. An out time already past says "at this rate: out any time now".
- **D2 The rate:** the latest reading divided by the time from the window's start to that reading. The start is `resets_at` minus the window's length (5 hours, 7 days). The reading's own time is used, not now. No history is needed and the rate is rough on purpose: holds, the pace line and the reserve switch aren't modelled. This is the same "at this rate" as Claude's own page.
- **D3 Too early to tell:** no line until 10% of the window has passed (30 minutes, about 17 hours), so a burst right after a reset doesn't say "out in 20 minutes" (on 26 Oct at 23:12 the 5-hour window read 46% after 22 minutes). Also no line when the reading is stale (`status` set) or missing.
- **D4 The meter shows it too:** a hatched ghost (`--ghost` over the meter's track) runs from today's fill to the projected use at the reset, capped at the end. It is neutral, never a status colour. The legend gets one line: "hatched: where the meter will be at the reset, at this rate".
- **D5 Claude only:** Copilot's month is paced by the runner and has never run out, so it gets no line. It is one call away if it ever needs one.
- **D6 Where the code goes:** a pure `forecast(value, read_at, resets_at, length, now)` in `factory_dashboard/overview.py`, beside `_reset_label`, returning the out time (or none) and the projected use at the reset. `WindowAllowance` gains the reading's `at` and the line's words. The line goes under f9-29's "on pace" words in `_partials/allowance.html`, so the ticket waits for f9-29.

Mock-up: [`f61-mockup/at-this-rate.html`](f61-mockup/at-this-rate.html).

## Tickets
| # | Slug | Who | Diff | After | What |
|---|------|-----|------|-------|------|
| 01 | at-this-rate | D | 3 | f9-29 | D1 to D6: the "at this rate" line and the ghost on Claude's two meters |
