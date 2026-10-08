# F33: overview now check-all how long

The planning thread behind F33's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 00:05

> overview now check-all how long
>
> does'nnt say for how long it's been running, but it does with other tasks. it'd be good to have an estimate of how long the currente now task is estimated to be finished, i believe we do that in other places

## The lead, 2026-10-08 00:07

> You're right. Check-all says nothing about time, and the planning room already has an estimate for "the next reply" that Now never uses. I've drafted a two-ticket plan on `plan/f33`, set aside until you approve it. The runner is idle on f33, so you don't need to pause the factory.
>
> 1. **Not a repeat.** I checked every open card. F10 (crates on the belts) is about the floor's motion during check-all, not its time. F17 is the menu's small "something's running" dot. F32 is about the 5-hour window gauge. No merge.
>    *Action: nothing.*
>
> 2. **Why check-all shows no time.** A job is a database row with a start time, which is why Now shows "Elapsed" for jobs. Check-all, the gates and the warm-up aren't jobs. For those, the runner only writes its words ("check-all · f6-06") with no start time. It also keeps no record of how long past ones took, so today there's nothing to show and nothing to estimate from.
>    *Action: ticket f33-01 (mine, because `runner/` is protected). The runner records when its own work started, plus one row each time it finishes, with how long it took.*
>
> 3. **Where the estimate already exists.** The planning room's "next reply ~4 min" (`_typical` in `factory_dashboard/planning.py`) averages the last 10 finished jobs of the same role and agent. Now has no estimate at all, even for jobs.
>    *Action: ticket f33-02 (developer) moves that one helper next to Now, so both pages always give the same estimate.*
>
> 4. **What Now will say.** For a job or the runner's own work, two lines:
>    - "Running for 2 min"
>    - "About 3 min left", or "Any minute now" within the last minute, or "Longer than usual (about 5 min)" once it's past the usual time.
>
>    With no history there's no estimate line. While paused or waiting for Claude's limit, neither line shows.
>    *Action: in f33-02.*
>
> 5. **A challenge: the job estimate is rough.** It averages by role and agent, so a small developer ticket and a big one get the same guess. I recommend keeping it this way for now: one estimate everywhere, and for check-all (the case you raised) it should be close, because check-all takes about the same time every run. If job estimates prove poor, the fix is one change in the shared helper (average by difficulty too). The other option is to do that now, which costs a bit more and isn't proven to be needed.
>    *Action: nothing now. Note it at review.*
>
> 1. **Not a repeat**: F10 is the floor's crates during check-all, F17 the menu's running dot, F32 the window gauge. None is about Now's time or estimate.
>    Action: nothing
> 2. **Why check-all shows no time**: Jobs have a start time in the database; check-all, the gates and the warm-up are only the runner's words, with no start time and no record of past durations.
>    Action: ticket f33-01 (lead, runner is protected)
> 3. **Reuse the planning room's estimate**: The planning room's 'next reply ~N min' averages the last 10 jobs of the same role and agent; Now has none.
>    Action: ticket f33-02 shares that one helper between both pages
> 4. **What Now will say**: 'Running for N min', then 'About N min left', 'Any minute now', or 'Longer than usual (about N min)'; no estimate without history, neither line while paused or waiting.
>    Action: in f33-02
> 5. **The job estimate is rough**: Averaging by role and agent ignores ticket size. Recommend keeping one shared estimate now; check-all's will be close. If job estimates prove poor, add difficulty in the shared helper later.
>    Action: nothing now; note at review
>
> Proposals:
> - F33: how long Now's work has run, and how long it has left (plan)
