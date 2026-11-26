# F300: Projects page: show the card you already asked for, not the plant button again

The planning thread behind F300's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-25 20:56

> the factory project page shouldn't say plant and ask the lead for a stack if i've already planted and it's being worked on

## The lead, 2026-11-25 21:23

> I've drafted the plan, a mock-up and two developer tickets for F300. Coaster-ranker is the case you saw: its stack card is already planned and ready, but its plate still shows the button.
>
> 1. **Why the button stays**: The page only checks whether a project has a stack, never whether you already asked for one. coaster-ranker's stack was planted on 24 November and became M13, 'Run coaster-ranker from the Projects page in Docker, retiring bin/live', which is ready. Its plate on /projects still says 'Plant and ask the lead for a stack'. Also, after you press, the button comes back on the next reload, until the runner picks the request up.
>    Action: The plan below fixes both.
> 2. **The plate shows the card you asked for**: Once you've pressed the button, the plate shows 'On its way…' with the dashed orange edge, and that stays after a reload. Once the card is planted, the plate shows a link to it: 'You asked the lead · M13 · its title · ready'. Tapping it opens the card's thread. The button comes back only if that card is done or removed and the project still has no stack. Nothing new is stored: the page reads the request and the card it became, which the runner already records.
>    Action: Ticket f300-01, built from the mock-up's coaster-ranker and coucou plates.
> 3. **The same for 'Plant and ask the lead to fix it', and Needs you clears**: The fix button for a crashed app has the same problem, so I've included it. Once you've asked for a fix, the app row shows the fix card instead of the button. The red lamp stays, because the app is still down. The crash also leaves Needs you, since you've already dealt with it.
>    Action: Ticket f300-02. Its picture is the mock-up's wardrobe-teller plate, which is an example: that app is only stopped tonight.
> 4. **Only the page's own button is recognised**: If you plant a stack or fix card yourself from the Plant box in your own words, the page won't connect it to the project and the button stays. Matching free text would mean guessing. If you press the button again anyway, the runner sees the card is already planted and doesn't plant it twice.
>    Action: Nothing, unless you want hand-planted cards recognised too.
> 5. **The mock-up**: Today and Proposed of /projects with tonight's real coaster-ranker and coucou plates. On a phone you flip between them; on a wide screen they sit side by side. The card link is drawn as a small factory work order (hazard-stripe tab, cut corner) using the existing theme only, with no new colour.
>    Action: Read .softfield/cards/f300-mockup/projects-asked.html; both tickets build from it.
>
> Proposals:
> - F300: a plate shows the stack or fix card you already asked for (plan)
> - F300 mock-up: a plate that already asked the lead (mockup)
