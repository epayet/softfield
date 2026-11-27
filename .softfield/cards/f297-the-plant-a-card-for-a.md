# Milestone F297: Projects page plant buttons also ask the lead

> **State:** done · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-27. Base: git tag `f297-the-plant-a-card-for-a-start`. Report: [`.softfield/reviews/f297-the-plant-a-card-for-a.md`](../reviews/f297-the-plant-a-card-for-a.md).
> Planted by the owner on 2026-11-25.

## Notes
The plant a card for a stack button doesn't ask the lead it just plants a seed I want it to ask the lead as well so that I don't have to wait for it to get planted then go to planning then ask the lead

## Expected outcome
Pressing "Plant a card for a stack" (or "Plant a card to fix it") on `/projects` plants the card **and** sends it to the lead, as the Planning room's "Plant and ask the lead" does: the lead's answer and plan arrive on the new card's thread with no further press.

## Done when
- both buttons send a `plant` request whose value has `"ask": true`
- their labels and their "on its way" line say the lead is asked
- the owner presses one on a project without a stack and finds the lead's reply on the new card's thread

## Decisions
- **D1. Builds on the Plant box's own flag.** The runner already reads `"ask": true` on a `plant` request (`runner/planner.py` `asks`) and queues the lead on the new card's thread. Only the dashboard changes: `plant_value` in `factory_dashboard/stacks_routes.py` sends `"ask": True`. Nothing new is built, so nothing becomes removable.
- **D2. Both buttons ask.** "Plant a card to fix it" (a crashed app, a failed update, on the plate and in Needs you) has the same wait; it uses the same `plant_value`, so it asks too.
- **D3. Wording.** Buttons: "Plant and ask the lead for a stack", "Plant and ask the lead to fix it". On its way: "On its way: the runner plants it and asks the lead at its next pick".
- **D4. No mock-up:** wording only; the row's layout, colours and states don't change.

## Tickets
- f297-01-stack-plant-asks-the-lead (developer)
