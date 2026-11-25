# F297: Projects page plant buttons also ask the lead

The planning thread behind F297's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-25 07:18

> The plant a card for a stack button doesn't ask the lead it just plants a seed I want it to ask the lead as well so that I don't have to wait for it to get planted then go to planning then ask the lead

## The lead, 2026-11-25 08:25

> I've drafted a plan for F297 on its plan branch: one small developer ticket. The "ask the lead" switch the Planning room's Plant box uses already exists, and the Projects page's buttons just send it turned off.
>
> 1. **Why it only plants**: The Projects page's plant buttons send the same request as the Planning room's Plant box, but with "ask the lead" set to false (`plant_value` in `factory_dashboard/stacks_routes.py`). The runner already handles "ask" set to true: it plants the card and starts the lead on that card's thread, the same as "Plant and ask the lead". So the fix is to flip that one value on the dashboard. Nothing changes in the runner.
>    Action: Ticket f297-01 (developer, small).
> 2. **The fix button too**: "Plant a card to fix it" (shown for a crashed app or a failed update, on the project's plate and in Needs you) uses the same function and has the same wait. I recommend it asks the lead as well, because a broken app is exactly when you want an answer without another step. The alternative is to change only the stack button.
>    Action: Same ticket, both buttons.
> 3. **The cost**: Every press now starts a lead planning job on Opus, about the cost of one answer in the Planning room. Before, nothing ran until you wrote on the card. If you sometimes want only the seed, the Planning room's plain Plant still does that.
>    Action: Nothing.
> 4. **New wording, no mock-up**: The buttons become "Plant and ask the lead for a stack" and "Plant and ask the lead to fix it". After a press they show "On its way: the runner plants it and asks the lead at its next pick". Only the wording changes, not the layout, colours or states, so I didn't draw a mock-up. Ask if you want one.
>    Action: In the ticket.
>
> Proposals:
> - F297, Projects page plant buttons also ask the lead (plan)
