# F293: The planner stops telling the owner what they already know

The planning thread behind F293's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-24 22:08

> A lot of conversation points are things that I already know I don't need to be told again like
> Accept the rule before approving the plan
> The ticket depends on ADR 52 -- waste of my time

## The lead, 2026-11-25 08:12

> I traced the noise to the planner's brief. On F282, F286 and F292 it spent a point telling you to accept the ADR before the plan, which the Approve button already enforces. I drafted one lead ticket that cuts that kind of point.
>
> 1. **Where these points come from**: In one evening, three threads each gave a point to 'accept the ADR before approving the plan': F282 (Drop the re-check after Copilot's checkpoint), F286 (Code reviews highlight simpler code) and F292 (No terminal commands on the Overview). Each also repeated it in the 'In short' text. Approve already refuses a plan whose ADR is still a draft, and the desk shows why. So the point tells you nothing. 'No mock-up' was also a point of its own nine times lately, mostly on cards with nothing on screen, where the brief asks for no point at all.
>    Action: Ticket f293-01 changes the planner's brief.
> 2. **A rule with examples, not a list of banned sentences**: A list of sentences goes out of date the day a new button arrives. The brief instead gets one rule: tell you only what you don't already know, and never how the dashboard's buttons work or what order to press them in. The three you've seen are its examples. A real choice inside an ADR still gets a point, like 'if you turn ADR 52 down, the plan loses f292-02'. That one tells you a cost.
>    Action: Part of f293-01 (D1).
> 3. **Two other points stay, on purpose**: I'm keeping the 'pause the factory first' point on replans. Without the pause, the line can start a ticket while it's being rewritten, and that work gets paid for twice. I'm also keeping the 'this project can't take pictures yet' point, which comes up rarely. Both ask you for something or warn you about a real cost. If you find them just as obvious, say so and the ticket removes them too.
>    Action: Nothing, unless you comment.
> 4. **No need for one button that does both**: Another fix would be for Approve to accept the ADR too. But then pressing Approve would also accept a rule. Accepting a rule is your own separate decision, and it should stay that way. Since the planner will stop talking about the order, the refusal message on the desk is enough.
>    Action: Nothing.
>
> Proposals:
> - F293: the planner stops telling the owner what they already know (plan)
