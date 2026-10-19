# F151: I had to restart the runner manually after f114-02, why.…

The planning thread behind F151's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-17 13:02

> I had to restart the runner manually after f114-02, why. It did a copilot checkpoint after that

## The lead, 2026-10-19 23:22

> I found why it stopped and drafted a one-ticket fix. Nothing is queued until you approve it.
>
> 1. **Why you had to restart after f114-02**: Claude's weekly limit was used up until Monday 19 October at 17:00. At 02:54 a checkpoint came due, Copilot did it in Claude's place, and the checkpoint then parked until Monday so Claude could check the same work again later. That part worked as designed. After that, five more tickets merged, the last being f114-02 at 11:55. The runner only starts a checkpoint when no checkpoint is waiting, and the parked one still counted as waiting, so Copilot never looked at those five. Every developer ticket still ready was waiting on a lead ticket, and every lead ticket was waiting on Claude. So from 11:55 the runner sat idle, and it would have stayed idle until Monday 17:00.
>    Action: Nothing on its own: the fix is point 3.
> 2. **Why your restart got it moving**: A restart retries every parked job straight away. Claude was still out, so Copilot reviewed the five merges at 13:02 and filed f114-03 to f114-06. Those fix tickets kept the line busy until 21:29. The original design already said Copilot should review each new batch while Claude is out. That rule is in the code but only works in a test that starts the job by hand. In the real loop, nothing started it before Monday.
>    Action: Written up in the card's 'What happened'.
> 3. **Fix: a new batch of merges starts the parked checkpoint again**: Once enough unchecked merges pile up while the checkpoint is parked, it runs again at the next pick, the same way a restart makes it run. If Claude is still out, Copilot reviews only the new merges, and the checkpoint parks again so Claude can re-check them all later. If Claude is free, Claude's checkpoint just runs sooner. It is one condition in the runner's own code, which only the lead may change, so it is a lead ticket with priority 1. That fits your first priority: the runner works on its own.
>    Action: Lead ticket f151-01-stand-in-on-each-batch.
> 4. **Related: F140, Copilot takes checkpoints first**: This is not a repeat. F140 changes who does checkpoints, and once it is built, a checkpoint would no longer park after Copilot does it, so this problem would go away there too. But F140 needs an ADR and has no plan yet, while this fix is small and stops the line from going idle now. When F140 is planned, it can remove this condition along with the parking.
>    Action: Keep the two cards separate; I'll mention this fix in F140's plan.
>
> Proposals:
> - F151: Copilot reviews each new batch while Claude is out (plan)
