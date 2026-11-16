# F252: The app's Open button on the Projects page opens a new tab

The planning thread behind F252's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-16 19:24

> make the open app with docker button in project page open in a new tab instead

## The lead, 2026-11-16 19:35

> I drafted one small ticket that makes the Projects page's Open button open the app in a new tab. It passes the ticket check, and nothing is queued until you approve the plan.
>
> 1. **Agreed: a new tab is better here**: When F239 (Run each project's app from the Projects page) built this button, its ticket said the button opens the app in the same tab. Your change is better. The app runs on a different port, so in the same tab the Projects page goes away. You then lose its live Run/Stop state and have to come back with Back, which is awkward on a phone. The ↗ on the button already says it takes you somewhere else. The dashboard's other outside links (Open the mock-up, the live page links on a card's page) already open a new tab, so this button will match them.
>    Action: One developer ticket, f252-01: the Open link gets target=_blank and rel=noopener. A test that checks for the same tab is changed to check for a new tab. Logs stays in the page.
> 2. **No mock-up**: Nothing on the page looks different. The button keeps its text, colour and place, and only where it takes you changes, so there is nothing to draw.
>    Action: Nothing. Ask if you want one anyway.
> 3. **Where it goes in the line**: It's a one-line change for a developer, under half an hour of work. Your card sits where the board puts it (priority 100, with the other new ideas). To have it soon, drag F252 near the top of the board.
>    Action: Nothing, unless you move the card.
>
> Proposals:
> - F252: Open the app in a new tab (plan)
