# F50: a finished card shows its review

The planning thread behind F50's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 08:55

> the data safety review it asks has no info

## The lead, 2026-10-08 09:07

> The F20 review you were asked for was empty because the dashboard asked too early. It listed F20 under "Finished, to talk through" as soon as its two tickets merged. F20's review is still in the queue and hasn't been written, so there was nothing to show. On top of that, the link opens F20's planning conversation, and F20 has none (it was planned in a terminal). So you got a title and an empty reply box.
>
> 1. **Why it was empty.** The dashboard treats a feature as finished when all its tickets are merged, without waiting for the review. The early mock-ups had it the other way round ("F2 is ripe: the review is done"). The conversation page also never shows a review summary; only the milestone page does, and nothing links to it. → Fixed by the plan in point 4.
>
> 2. **Does F20 work?** Yes, I checked both parts. The first daily backup is in `~/Dropbox/software-factory-backups/` (`factory-metrics-20261008-0820.sqlite`). Five approved planning conversations are saved in `docs/planning/` (F22, F28, F30, F32, F41). To check for yourself: open that Dropbox folder, and look at `docs/planning/f32-the-5-hour-lead-s-window.md`. → Nothing to do.
>
> 3. **When to sign F20 off.** I recommend waiting for its review. It's queued and should run after the current planning jobs. F20 changes the runner's own code and is about losing data, so it's worth checking. Then sign off with `uv run runner signoff 20`, or with the new button once this plan lands. → Nothing to do now.
>
> 4. **The plan: a finished card shows its review.**
>    - A card is listed as finished only once its review is written. Until then it stays with the cards being built, and the queue shows "review F20".
>    - Its page then opens on three parts of the review: what changed, how to test it, and any decision waiting for you. A link leads to the whole review.
>    - A Sign off button on that page shows "signing off at the runner's next pick" at once.
>    - Three small developer tickets (difficulty 2, 3, 2), all in the dashboard code, each copying an existing example in the code. → Approve the plan.
>
> 5. **The Sign off button is new.** Today the dashboard can't sign anything off, although the runner already accepts a sign-off request from it. You've said reviewing features from the dashboard is your third priority, and this is the part that's missing. The button doesn't skip any check: the runner still refuses if tickets are left, and waits if the repo has uncommitted changes. If you'd rather keep sign-off in the terminal only, I'll drop ticket 03. → Keep it.
>
> 6. **No repeat, and a priority.** No other card or conversation covers this. The closest are F35 (a "next" button on the desk) and F21 (the lead's briefs), and neither touches finished cards. I gave F50 priority 2, just behind F20, F21 and F31, because every feature you finish from now on will hit the same empty page. → Change it if you want it lower.
>
> Nothing touches tickets that are already queued, so you don't need to pause the factory.
>
> 1. **Why it was empty**: The dashboard lists a feature as finished as soon as its tickets are merged. F20's review is still queued, so there was no review to show. The link opens F20's planning conversation, and F20 has none (it was planned in a terminal). The conversation page never shows a review summary anyway; only the milestone page does, and nothing links to it.
>    Action: Fixed by the F50 plan (point 4).
> 2. **Does F20 work?**: Yes. The first daily backup is in ~/Dropbox/software-factory-backups/ (factory-metrics-20261008-0820.sqlite), and five approved planning conversations are saved in docs/planning/ (F22, F28, F30, F32, F41). To check: open that Dropbox folder, and look at docs/planning/f32-the-5-hour-lead-s-window.md.
>    Action: Nothing.
> 3. **When to sign F20 off**: Wait for its review: it's queued and runs after the current planning jobs. F20 changes the runner's own code and is about losing data, so the check is worth having. Then run `uv run runner signoff 20`, or use the new button once F50 lands.
>    Action: Nothing now.
> 4. **The plan: a finished card shows its review**: A card is listed as finished only once its review is written. Its page then opens on what changed, how to test it and any decision waiting, with a link to the whole review, and has a Sign off button. Three small developer tickets in the dashboard code.
>    Action: Approve the F50 plan.
> 5. **The Sign off button is new**: Today the dashboard can't sign anything off, though the runner already accepts a sign-off request from it. Reviewing features from the dashboard is your third priority; this is the missing part. The runner's checks stay: it refuses with tickets left and waits while the repo has uncommitted changes.
>    Action: Keep ticket f50-03; I drop it if you want sign-off in the terminal only.
> 6. **No repeat, and a priority**: No other card or conversation covers this (F35 is a 'next' button on the desk, F21 the lead's briefs). F50 gets priority 2, just behind F20, F21 and F31: every feature you finish from now on hits the same empty page.
>    Action: Nothing, unless you want it lower.
>
> Proposals:
> - F50: a finished card shows its review (plan)
