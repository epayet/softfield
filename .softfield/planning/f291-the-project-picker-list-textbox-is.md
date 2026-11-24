# F291: The project picker's open list reads grey on white in the dark theme

The planning thread behind F291's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-24 08:44

> the project picker list textbox is grey on white, hard to read. where does that come from

## The lead, 2026-11-24 13:28

> I found the cause, and the fix is one small ticket for a developer. I ran `softfield check-tickets` on it and it passed.
>
> 1. **Where the grey on white comes from**: It came in with F256, the alignments of the top bar (ticket f256-01). To make the picker look like one plate with its 'Project' label, that ticket made the picker's background transparent (dashboard.css, rule `.bar-top .filters select`). When the list opens, the browser draws it on the picker's own background, and a transparent background turns into white there. The text keeps the dark theme's ink, a light grey (#dfe4e8), so you get light grey on white. The light theme's dark text on white reads fine, so only the dark theme is affected. The picker is the only control on the dashboard with a transparent background; the others (replay, timeline, logs) already sit on the plate colour.
>    Action: Fix it with ticket f291-01 (point 2).
> 2. **The fix: the picker gets the plate colour**: The picker's background becomes the plate colour, the same as its label, so the closed picker looks exactly as it does now. Its options get the plate colour with the theme's ink, so the open list reads well in both themes. It uses colours the theme already has, no new ones. It's small and copies the other controls' rule, so it goes to a developer. The test reads the colours the browser actually draws in both themes, checks the closed picker keeps its size at 1440 px and 390 px, and checks picking a project still reloads the page.
>    Action: Ticket f291-01-picker-list-readable, for a developer, in the plan below.
> 3. **No mock-up**: This puts back the look the picker was always meant to have: readable options in the theme's colours. Nothing on the page moves or changes, so I haven't drawn a mock-up. If you want a picture of the open list before and after, ask here.
>    Action: Nothing.
>
> Proposals:
> - F291: the project picker's open list follows the theme (plan)
