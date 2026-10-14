# F69: I want a button to switch from light to night theme

The planning thread behind F69's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 08:41

> I want a button to switch from light to night theme

## The lead, 2026-10-09 08:48

> I've drafted F69 as one small developer ticket. The dashboard already has a night theme and a light one, but today it only follows your device's setting. The ticket adds a button that overrides that on each device, and the charts redraw when you switch.
>
> 1. **What you get**: A button in the top bar of every dashboard page switches between night and light at once, charts and the factory floor included, with no reload. Its label names the theme it switches to: "Night" while light is showing, "Light" while night is showing.
>    Action: Ticket f69-01-theme-button (developer, difficulty 3)
> 2. **Each device remembers its own choice**: Your phone and your desktop each keep their own choice, in the browser. Until you press the button, a page follows your device's setting, as it does now. I recommend this over saving the choice on the server: a theme belongs to a screen, and it's nothing we'd need to back up.
>    Action: In the ticket
> 3. **Two states, no "follow my device" option**: Once you press it, the choice stays until you press it again. If your phone already switches to dark on its own at night, you may not need the button there at all. A three-way choice (Device / Light / Night) would add a second click and more words to a crowded top bar. I recommend the simple two-way button; say so if you'd rather have the three-way one.
>    Action: Nothing unless you disagree
> 4. **The phone's top bar doesn't get taller**: On a phone, the button shares the line with the title and the project picker, so what's running stays above the fold.
>    Action: In the ticket's Done when
> 5. **No flash of the wrong theme**: A tiny script sets the theme before the page draws, so a page never flashes dark before turning light. The stylesheet stops reading the device setting directly; one existing test changes to match.
>    Action: In the ticket
>
> Proposals:
> - F69: a button to switch between light and night (plan)
