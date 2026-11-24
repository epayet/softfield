# F285: Copilot pre-reviews a finished milestone while Claude is out

The planning thread behind F285's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-21 05:04

> I think I said at some point don't do a checkpoint just before a review but if I'm out of Claude tokens, copilot could do one checkpoint in case it finds things that the developer can fix before the next review when Claude is back, this should make a stronger case to review. It shouldn't go on an infinite loop of Dev work - Claude out - copilot checkpoint - dev fix - Claude out - copilot checkpoint - new dev fix etc but up to 3 times would be good.
>
> This is for when let's say Claude is out of tokens on Friday so we can take more time to make the dev tickets a bit better for when Claude is back
>
> So I think priority order is something like:
> - every 2 dev tickets and there are more dev tickets coming: checkpoint (Claude if available, copilot otherwise unless we think copilot is good for this under copilot pacing rules)
> - last dev ticket before review and there are other dev tickets to do: pick up other dev tickets
> - no more dev tickets and a few tickets at ready for review but Claude is out: checkpoint
>
> What I wrote above might not be completely right, but I think I have a better idea now. Let's introduce a new type of job (better name to be found): optional dev quality check, done by copilot. This job will only happen when all the dev work is done and Claude is not available. It will basically act as a checkoointer to find issues Devs could fix before Claude is back. Less important than already defined dev work, this job can make dev tickets. Not more than 3 times per milestone. Goal is that rather than having factory idle it could improve things

## The lead, 2026-11-23 22:33

> I've drafted ADR 51 and a three-ticket plan for a Copilot "pre-review" that only runs when the line would otherwise sit idle.
>
> 1. **Your first list is mostly how it works already**: A checkpoint already runs every two developer merges. When Claude is limited, Copilot does it instead: 8 times this month, the last on 21 Nov (job 2611). A review that waits for Claude doesn't hold up other developer tickets either; the queue goes on. What's missing is your last case: every developer ticket is done, reviews wait for Claude, and the line sits idle. Since F264, The factory should never stay idle, only Claude's real limit (100%, or a rest after a refusal) stops lead work, so that idle case is exactly your Friday.
>    Action: Nothing. The plan only covers the idle case.
> 2. **A new job: Copilot's pre-review of a finished milestone**: When Claude is at its real limit and nothing else can start, Copilot reads one milestone whose review waits for Claude. It reads the whole milestone, not just the last two merges: the card's Expected outcome, Done when and Decisions, its done tickets, and every file they changed. Then it files developer fix tickets. This is a deliberate exception to F162, No checkpoint on merges the milestone's review is about to read. That rule assumed the review comes straight away, which isn't true when Claude is out until Monday.
>    Action: ADR 51 items 1–2; tickets f285-01 and f285-02.
> 3. **Its name**: I recommend "pre-review": it says when it happens and what it leads to, and it sits well next to "checkpoint" and "review" on the floor. Other options: (a) "tidy-up pass", (b) "Copilot's look", (c) your "dev quality check".
>    Action: Tell me if you'd rather another name; it is only words in the ADR, the tickets and two dashboard labels.
> 4. **Which milestones it reads**: I recommend only milestones whose tickets are all done and whose review waits for Claude, as you wrote ("when all the dev work is done"). The alternative is to also read a milestone that still has lead tickets waiting for Claude. That covers most Softfield milestones, since `runner/` is protected, so it would run more often. But Copilot would be judging half-built work, and its fixes could collide with lead tickets still to come.
>    Action: As recommended unless you say otherwise. The other option can be added later as one line in ticket f285-02.
> 5. **Three per milestone, and no rerun without new work**: At most three pre-reviews per milestone, as you asked, counted from their finished jobs. I also added a stop: a milestone gets another pre-review only after a new merge since its last one. So a pre-review that finds nothing ends them until Claude is back, instead of using up all three rounds rereading the same code.
>    Action: ADR 51 item 4; ticket f285-02.
> 6. **It stays within Copilot's pace line**: Copilot's month is 10% used, and each job costs about one credit. The pre-review stays under its pace line rather than its full cap. That way it never uses up the room the checkpoint stand-in needs when Claude is limited.
>    Action: ADR 51 item 5; f285-01 adds a pace-line option to the existing Copilot routing.
> 7. **The risk: Copilot's false alarms become developer work**: On the bench Copilot found about 1 in 5 known problems and raised false alarms. Each finding it files becomes a developer ticket that makes the diff longer. There is also a delay cost: if Claude comes back while those fixes are still waiting, the review waits for them, at about 46 minutes each lately. In return, the Opus review judges every pre-review finding (kept, wrong, missed). That gives you the record of how good Copilot is that you wanted for the factory reviews on F140, Copilot does the checkpoints first.
>    Action: Accepted cost, written in ADR 51's Consequences. Review it after a few weekends.
> 8. **Developer tickets only**: Claude is out, so a lead ticket couldn't run anyway. A finding that would need the lead (a protected file, or a fix of a fix) files no ticket. It is recorded for the review to deal with.
>    Action: ADR 51 item 3; ticket f285-01.
> 9. **No mock-up**: Nothing is added, moved or removed on any page. The new job shows on the existing rows, with two new labels: "Copilot reads F… before the lead's review" and "Copilot's pre-reviews".
>    Action: Ticket f285-03 (developer). Ask if you want a picture anyway.
> 10. **Accept ADR 51 before the plan**: The two lead tickets rely on ADR 51, so their pre-flight check refuses them until the ADR is Accepted. That is the only problem the check reports.
>    Action: Approve ADR 51 first, then the plan.
>
> Proposals:
> - ADR 51: Copilot pre-reviews a finished milestone while Claude is out (adr)
> - F285 plan: the pre-review, when it runs, its words (plan)
