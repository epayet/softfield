# F28: the first time i clicked on the pause button nothing happened, but then eventually it worked

The planning thread behind F28's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-07 23:10

> the first time i clicked on the pause button nothing happened, but then eventually it worked

## The lead, 2026-10-07 23:29

> 1. **Why the first click seemed to do nothing.** It wasn't your tap. Every page refreshes the top bar every 5 seconds. When you press Pause, the bar shows "Pausing after this job" straight away. But a refresh that started just before your click arrives a moment later with the old state ("Running" and a Pause button) and draws over it. Saving the request can also wait up to 10 seconds while the runner is writing to the database, so one or two refreshes can land first. The next refresh then shows the pause, which is the "eventually it worked" you saw. Our test for this button turns the refresh off, which is why it never caught this. **Action:** ticket f28-01. After a click, the bar ignores refreshes that still show the old state, so "Pausing after this job" or "Resuming…" stays until the runner agrees.
>
> 2. **A request that never arrives should say so.** At the moment, if the request fails, the bar shows "Pausing…" and then quietly goes back to how it was. **Action:** also in f28-01. It will show "Didn't reach the factory: try again" and put the button back.
>
> 3. **F29 is the same bug, on Overview.** The Now panel has its own Pause/Resume button with the same refresh problem, and it never says "Resuming…". That's what F29 describes: the top bar said "Resuming…" while Now still offered Resume. **Action:** merge F29 into F28 (proposal below).
>
> 4. **I'd remove the second button rather than fix it.** The top bar has had Pause/Resume on every page since f6-16, so the button in Now repeats it. Two buttons means two things that can disagree, which is exactly F29. Now would keep only the status line ("Pausing after this job", "Paused by you since…", "Resuming…"). **Action:** ticket f28-02. If you'd rather keep the button in Now, say so; it would then need the f28-01 treatment too.
>
> 5. **Related cards I'm keeping separate.** F17 changes how the button looks (an icon instead of words) and builds on this one button, so it's simpler after F28. F27 (planner jobs shouldn't stop when you pause) is a different change. **Action:** none.
>
> 6. **One check: which "eventually" did you mean?** If the bar did say "Pausing after this job" but the job kept running for a while, that's by design: a pause waits for the current job to finish. The fix in points 1–2 is for the case where the bar went back to Pause. **Action:** none, unless it was the first case.
>
> 7. **Plan and tickets.** Two developer tickets, difficulty 4 and 2, in `tasks/later/`, so nothing is queued until you approve. Nothing is in `tasks/ready/`, so you don't need to pause the factory for this.
>
> 1. **Why the first click seemed to do nothing**: The 5-second refresh of the top bar draws the old state ('Running' and Pause) over the 'Pausing after this job' your click showed. Saving the request can also wait up to 10 s while the runner writes. The next refresh then shows the pause. The test for this button turns the refresh off, so it never caught this.
>    Action: Ticket f28-01: after a click, ignore refreshes that still show the old state
> 2. **A request that never arrives should say so**: If the request fails, the bar goes back to how it was without saying anything.
>    Action: In f28-01: show 'Didn't reach the factory: try again' and put the button back
> 3. **F29 is the same bug, on Overview**: Now on Overview has its own Pause/Resume with the same refresh problem, and no 'Resuming…' state, so the top bar said 'Resuming…' while Now still offered Resume.
>    Action: Merge F29 into F28
> 4. **Remove the second button rather than fix it**: The top bar has Pause/Resume on every page, so Now's button repeats it, and two buttons can disagree (F29). Now keeps only its status line, with 'Resuming…' added.
>    Action: Ticket f28-02
> 5. **F17 and F27 stay separate**: F17 changes how the button looks and builds on this one button; F27 (planner jobs not paused) is a different change.
>    Action: Nothing
> 6. **Which 'eventually' did you mean?**: If the bar did say 'Pausing after this job' but the job kept running, that's by design: a pause waits for the current job to finish. This fix is for the case where the bar went back to Pause.
>    Action: Nothing, unless it was the first case
> 7. **Plan and tickets**: Two developer tickets, difficulty 4 and 2, in tasks/later/. Nothing in tasks/ready/ changes, so there's no need to pause the factory.
>    Action: Approve the plan
>
> Proposals:
> - F28: pause and resume show what you asked, even through the refresh (plan)
> - F29 (top bar said Resuming, Overview still offered Resume) joins F28 (merge)
