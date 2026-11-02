# F153: Sonnet does the easier lead tickets, Opus keeps planning and checks

The planning thread behind F153's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-20 07:40

> I wonder if sonnet would be good enough to do the lead tickets. And keep opus for planning, sonnet for execution.

## The lead, 2026-10-20 07:50

> I drafted ADR 32 as a measured trial, plus the card's Decisions and two lead tickets that build the switch. Nothing changes until you accept the ADR and approve the plan.
>
> 1. **Is Sonnet good enough for lead tickets? Nobody knows yet, so try it and measure**: Sonnet has never done a lead ticket. Opus has done all of them since F1: 51 passed and 3 failed since 2026-10-06, at $2.35 each. What we do know about Sonnet is good: 3 out of 3 first time as a developer, and real bugs found as the checkpoint. Lead tickets cost $120 of Claude's $438 in those two weeks (27%). Planning, which you keep on Opus, cost $195 (44%). The bigger gain is time: on 2026-10-19 five Claude jobs waited until 17:00 at the 5-hour limit, which Opus and Sonnet share. Opus uses up that limit faster for the same work.
>    Action: ADR 32: a trial on the easier lead tickets, read again at the next factory review after about 15 Sonnet tickets. Then widen it, keep it or go back.
> 2. **The hidden cost: today nobody checks a lead ticket before the milestone review**: A lead ticket gets one attempt. If check-all fails, it is blocked. Its merge never goes to a checkpoint (only developers' merges do), so the first look is the Opus milestone review at the end. That was fine with Opus writing protected and security code. With Sonnet writing it, I wouldn't leave it unchecked. So: Opus checkpoints Sonnet's merges, using the existing rule that a checkpoint runs on another model than the author. And a Sonnet ticket that fails check-all gets one Opus attempt before it is blocked, the same step-up developers have. Both eat into the saving, which is why the trial measures dollars per ticket including them, not list prices.
>    Action: Decisions D2 and D3 on the card, built by ticket f153-02.
> 3. **Question: which lead tickets go to Sonnet?**: Recommended: difficulty 4 or below. That covers about two thirds of recent lead tickets (23 of 34 in F12 to F114), and Opus keeps the 5+ ones: new modules, security, schema. Other choices: (b) 3 or below, about a third, safer and a slower answer; (c) every lead ticket, the biggest saving and the biggest risk. The limit is one setting, so it can change during the trial without a ticket.
>    Action: ADR 32 item 1 and D1, with 4 unless you choose otherwise.
> 4. **Question: should Opus check Sonnet's lead tickets?**: Recommended: yes, at the next checkpoint (point 2). It costs one Opus checkpoint per batch of merges. Alternative: no check, the same as Opus's lead tickets today. That is cheaper, but a Sonnet mistake in protected code would wait for the milestone review.
>    Action: ADR 32 item 2, kept unless you say no.
> 5. **'Sonnet for execution': escalations and directions stay on Opus for now**: Since 10-06, escalations cost $34 and directions $26. Both judge someone else's failed work, which is where Opus earns its price. Moving them would change two things at once and blur the trial's result.
>    Action: Look at them again when the trial is read (ADR 32 item 6).
> 6. **The switch is two lines of the machine's settings, set after the tickets land**: Once f153-01 and f153-02 are on main, two lines in ~/.config/softfield/factory.toml turn it on: lead-ticket lists Sonnet then Opus, and lead_first_up_to = 4. A headless job can't write that file, so I set the lines in the next terminal session (or you do). Going back is the same two lines. With today's settings the new code changes nothing.
>    Action: Decision D7; nothing for you to do until then.
> 7. **No mock-up**: Nothing on a page changes. The board and reports already show who did each ticket, and they will simply say claude-sonnet where Sonnet worked.
>    Action: Nothing.
> 8. **To go ahead: accept ADR 32 first, then approve the plan**: Both tickets rely on ADR 32, so pre-flight refuses them while it is Proposed. Answer points 3 and 4 (or say nothing to take my recommendations). I'll fold the answers into the ADR, then press Accept on ADR 32 and Approve on the plan. The two tickets run on Opus, about $5, and queue behind the cards already ready.
>    Action: Your Accept, then Approve.
>
> Proposals:
> - ADR 32: Sonnet does the easier lead tickets, checked by Opus (adr)
> - F153: Sonnet on the easier lead tickets (plan)

## The owner, 2026-10-20 09:10

> I sent back your proposal “ADR 32: Sonnet does the easier lead tickets, checked by Opus” (adr-32).
> - On its key point 2 (Opus checks Sonnet's lead merges): no checkpoint needed

## The lead, 2026-10-20 09:12

> I folded "no checkpoint" into ADR 32 and cut the checkpoint part out of the card and of ticket f153-02. Apart from the expected "accept ADR 32 first" message, pre-flight passes on both tickets.
>
> 1. **No checkpoint on Sonnet's lead tickets: done, with one risk to know**: Agreed. It keeps the saving whole and treats Sonnet's lead tickets the same as Opus's. The risk you're accepting: a flaw that passes check-all is first seen at the milestone review, and later tickets may already have built on it. The Opus step-up after a failed check-all stays; it only catches work that fails the checks. The trial now compares what the milestone reviews find in Sonnet's lead work against Opus's, and that comparison is where we'd stop the trial if Sonnet's work shows more problems.
>    Action: ADR 32 item 2 rewritten and recorded under 'Settled with the owner'; card Decision D2 and ticket f153-02 trimmed to match.
> 2. **To go ahead: accept ADR 32, then approve the plan**: Both tickets rely on ADR 32, so Approve on the plan works only once the ADR is accepted. Difficulty 4 counts as agreed, since you didn't comment on it.
>    Action: Press Accept on ADR 32, then Approve on the plan.
>
> Proposals:
> - ADR 32: Sonnet does the easier lead tickets, Opus steps in when it fails (adr)
> - F153: Sonnet on the easier lead tickets (plan)
