# F282: The re-check row says Copilot already did the checkpoint while Claude was out

The planning thread behind F282's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-21 04:19

> This was in the queue while Claude was out of memory: Checkpoint: f275-a-project-created-by-web-interface · Claude re-checks f62-03-projects-planning-jobs-name-the-card and f275-02-start-plate-on-top, after a stand-in · waits until Mon 23 Nov 16:00 · softfield
>
> Isn't copilot doing checkpoints in this case?

## The lead, 2026-11-23 22:19

> I've answered the question from the run records and drafted one small ticket so the queue row says plainly that Copilot already did the checkpoint.
>
> 1. **Yes, Copilot did that checkpoint**: Copilot did it. On 21 Nov at 01:36, while Claude was limited, copilot-auto reviewed f62-03 (projects page planning jobs name the card) and f275-02 (start plate on top) in a minute and a half (job 2611). It found three real problems: a planner reply that doesn't name its card in coming.py, a link to the wrong project on the Projects page, and tests that only check that something appears somewhere on the page. Each became a fix ticket: f62-04 and f62-05 are ready, and f275-03 is already merged. The row you saw is the second step of the rule (ADR 16 item 9): Claude checks the stand-in's review again once its limit resets. That row is parked and holds up nothing. Other work kept going past it.
>    Action: Nothing. The ticket in point 3 fixes the wording that hid this.
> 2. **I'd keep Claude's re-check**: Copilot's three findings here are good. On its earlier trial against a Claude checkpoint, though, it caught 2 of 5 problems (runner/instructions/author/known-range.md), so it isn't yet good enough to be the only check. The re-check runs on Sonnet for about $0.20–0.30. It is also skipped on its own when the card's review is coming soon to read those merges (ADR 38). For example, f275-02 drops out once F275, A project created on the Projects page goes first, finishes f275-01. Whether Copilot should do more on its own when Claude is out is what F285, A Copilot quality check when the dev work is done and Claude is out, is about. That's the place to decide whether to drop the re-check, once Copilot has a few more checkpoints on record.
>    Action: Nothing here. Take the question up when F285 is planned.
> 3. **The row's wording hid that the checkpoint was done**: "Claude re-checks f62-03 and f275-02, after a stand-in" reads as if Claude does the checkpoint and nobody did it before. The runner doesn't even keep which agent stood in. One small lead ticket (the runner's code is protected) keeps the stand-in's name and changes the row to: "Claude checks again copilot-auto's review of f62-03… and f275-02…, done while Claude was out". It's a wording change only, so no mock-up.
>    Action: Ticket f282-01-recheck-row-names-the-stand-in, in the plan below.
>
> Proposals:
> - F282: the re-check row names who stood in (plan)

## The owner, 2026-11-24 08:26

> On point 2: i disagree. remove the known range thing that's old. no need to re checkpoint if copilot took over and did checkpoint. claude will catch whatever's left in the next checkout if it can or the review

## The lead, 2026-11-24 13:18

> I've switched to your call: Copilot's checkpoint is final, and Claude no longer checks it again. That changes a workflow rule, so it's a short new rule document (ADR 52) for you to accept, plus one lead ticket that carries it out.
>
> 1. **Agreed: no re-check after Copilot's checkpoint**: You're right. Claude's next checkpoint reads the merges that follow, including Copilot's fix tickets, and the card's review reads the whole card anyway (ADR 38). So the re-check pays for a Sonnet run, about $0.25, to read code the review reads again later. It also puts a row in the queue that looks like the checkpoint was never done. The one cost: a problem Copilot misses can sit until the review, and later tickets may build on it. The review sees it all and files the fix, so I accept that.
>    Action: ADR 52 states the rule; ticket f282-01 removes the re-check from the runner.
> 2. **The old Copilot benchmark goes**: The "2 of 5" line in the lead's notes on what the agents can do (known-range.md) dates from 2 Oct and was the reason for the re-check. The same ticket deletes it. From now on, Copilot's record comes from how the reviews rate its findings, as ADR 51 (Copilot pre-reviews a finished card while Claude is out) already does.
>    Action: Part of ticket f282-01.
> 3. **Accept the rule before approving the plan**: The ticket depends on ADR 52, so the plan's Approve will refuse it while the rule is still a draft. Accept ADR 52 first, then approve the plan. Until the ticket is merged, a re-check already in the queue may still run once.
>    Action: Accept ADR 52, then approve the plan.
>
> Proposals:
> - ADR 52: Copilot's stand-in checkpoint is final (adr)
> - F282: no re-check after Copilot's checkpoint (plan)
