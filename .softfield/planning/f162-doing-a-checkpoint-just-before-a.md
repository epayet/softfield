# F162: No checkpoint on merges the milestone's review is about to read

The planning thread behind F162's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 09:31

> I've drafted ADR 38, which changes ADR 12 item 8 so the runner stops checkpointing merges the review is about to read, plus one lead ticket for it. The ticket waits until you accept the ADR.
>
> 1. **You're right: the last checkpoint repeats the review**: From 15 to 23 October, about a dozen checkpoints ran on a milestone's last merges, and its review started right after, often within seconds. Examples: m1-first-suggestions (job 1146, then its review 1147 a tenth of a second later), F23, When I click comment (970 then 971) and F8, Images suggested (1238 then 1239). Each cost $0.13–0.30 and about a minute. The review then reads the same diffs again, as part of the whole milestone on Opus, and judges what the checkpoint found. A checkpoint is only worth something when later tickets of the same milestone build on what it checked, and after the last ticket there are none.
>    Action: ADR 38 and ticket f162-01
> 2. **The same happens between review rounds**: When a review writes fix tickets, its next round reads exactly those fixes. Yet the fixes got their own checkpoints too: m1-first-suggestions had two between its rounds (jobs 1142 and 1146). The rule covers this case as well.
>    Action: ADR 38 item 1
> 3. **Merges from other milestones keep their checkpoint**: One checkpoint can read merges from two milestones. Only the merges whose own milestone's review comes next are left out. If the others still add up to two merges, a checkpoint runs on them as it does today.
>    Action: ADR 38 item 2
> 4. **What it costs: the saving is small**: About $2–3 a week, plus the review starting a minute or so sooner. When the last checkpoint would have queued a fix (F6, I like the thing that says, did), the review's first round queues it instead: the same work, found by Opus rather than Sonnet. The checkpoint's rating also gets fewer samples. All of this is cheap, and the change cuts a step you read as waste on every milestone's last line, so I'd still do it.
>    Action: nothing
> 5. **One lead ticket, no mock-up**: `runner/` is protected, so the lead builds it. Nothing changes on screen: the checkpoint just stops appearing in the queue, and the run's log gets one line saying why it was left out.
>    Action: ticket f162-01-no-checkpoint-before-review, queued once ADR 38 is accepted
>
> Proposals:
> - ADR 38: No checkpoint on merges the milestone's review is about to read (adr)
> - F162: one lead ticket (plan)
