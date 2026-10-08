# F32: the 5 hour lead's window gauge on planning does'n say when it resets

The planning thread behind F32's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 00:04

> the 5 hour lead's window gauge on planning does'n say when it resets

## The lead, 2026-10-08 00:05

> 1. **Why the reset time is missing.** The data is already there. Every window's reset time is worked out for the Overview page ("resets at 17:00", or "resets on Oct 9 12:00" when it's on a later day). The lead's window on `/planning` only prints the percent, so one line is missing from the page. Nothing new needs to be measured. *Action:* plan F32 with one small developer ticket.
>
> 2. **Not a repeat, but it touches the same tile as f9-28.** None of the idea, planning or ready cards or the other threads talks about reset times. But ready ticket f9-28 (in F9) is about to add a week row to this same lead's window. If F32 went first, the two would clash. So F32's ticket waits for f9-28 and shows the reset on both rows, the 5-hour one and the week. *Action:* the ticket depends on f9-28. There's no merge, and F9 doesn't change. Nothing is waiting in F32 yet and its ticket goes in `tasks/later/`, so you don't need to pause the factory.
>
> 3. **One more fix while we're in there.** When the 5-hour window has reset and no new reading has come in, the tile shows an empty bar and "–", which looks like 0%. I'd have it say "reset since, no new reading", or "no data yet" when there's no reading at all. The Overview already shows those words. *Action:* included in the ticket.
>
> 4. **A clock time rather than a countdown.** You might prefer "resets in 1 h 20", which is easier to read at a glance. But the planning page doesn't refresh itself, so a countdown would quietly go wrong on a page left open. "Resets at 17:00" stays true. It's also the Overview's wording, so the two pages agree. *Action:* clock time only. If you want a countdown, it would need a live tile, which is a separate ticket.
>
> 1. **Why the reset time is missing**: The reset time is already worked out for each window (the Overview shows it); the lead's window on /planning only prints the percent. It's a missing line on the page, not missing data.
>    Action: Plan F32 with one developer ticket, f32-01-lead-window-resets.
> 2. **Not a repeat, but f9-28 changes the same tile**: No card or thread repeats this. Ready ticket f9-28 adds a week row to the same lead's window, so building F32 first would clash with it.
>    Action: f32-01 waits for f9-28 and shows the reset on both the 5-hour and week rows. No merge, F9 unchanged, no pause needed.
> 3. **Out-of-date readings say so**: After a reset with no new reading, the tile shows an empty bar and '–', which looks like 0%. It will say 'reset since, no new reading' or 'no data yet' instead, as the Overview does.
>    Action: Included in f32-01.
> 4. **A clock time, not a countdown**: A countdown ('in 1 h 20') would go wrong on a planning page left open, because that page doesn't refresh itself. 'Resets at 17:00' stays true and uses the Overview's wording.
>    Action: Clock time only; a countdown would need a live tile, as a separate ticket.
>
> Proposals:
> - F32: the lead's window says when it resets (plan)
