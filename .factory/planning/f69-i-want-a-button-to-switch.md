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

## The lead, 2026-10-09 20:34

> Approved by the owner on 2026-10-09: approved plan/f69: queued f69-01-theme-button

## The owner, 2026-10-28 08:53

> Works but how to make it more in the project theme I don't want to just have words I want a nice image button

## The lead, 2026-10-28 08:56

> I've drawn the button as a themed switch: a moon and a sun on a metal plate, with a yellow knob over the theme that's on. The picture is in the mock-up, and one small ticket builds it. Its pre-flight check passes.
>
> 1. **The image button: a moon-and-sun switch**: In place of the grey word "Light", the top bar gets a small switch on a metal plate with a cut corner. The moon is on the left, the sun on the right, and the hazard-yellow knob sits over the theme that's on, the same yellow as the page tab you're on. Pressing it slides the knob across and switches the theme. In the mock-up you can press the switches and flip Today and Proposed.
>    Action: Mock-up .factory/cards/f69-mockup/theme-switch.html
> 2. **Why a switch rather than a single icon**: The simpler option is one square button like Pause, showing a sun or a moon. It's in the mock-up as the calmer variant. The catch is that a sun on the night page can read as "it's day now" as easily as "tap for day". The switch shows both themes and which one is on, so it never reads backwards. I recommend the switch. Say "the single icon" if you prefer the smaller one.
>    Action: Nothing unless you choose the single icon
> 3. **Words stay where you can't see them**: The switch has no words on it now, but hovering still says "Switch to the light theme", and a screen reader hears "Night theme, on". That keeps the rule that every mark explains itself without putting a label on the bar.
>    Action: In the ticket
> 4. **On the phone**: It keeps its place on the top bar's single row and is 44 px tall, easy to hit with a thumb. The bar doesn't get taller, so what's running stays at the top. The project picker gives up the extra width, as it does today.
>    Action: In the ticket
> 5. **One small ticket, built by a developer**: f69-07, The theme button becomes a moon-and-sun switch: a developer ticket, difficulty 3, changing only the top bar's markup, its CSS and the theme tests. After you approve, it goes into the queue with F69, I want a button to switch from light to night theme, at priority 100, behind about 77 ready tickets, so it's a while off unless you drag the card up the board. Note: the first button took five follow-up fixes, all to the tests, over about four days. This ticket says exactly what the tests must check, so it shouldn't repeat that.
>    Action: Ticket f69-07-theme-switch-plate
>
> Proposals:
> - F69: the theme switch in the top bar (mockup)
> - F69: the button becomes a moon-and-sun switch (plan)

## The owner, 2026-10-29 01:17

> On point 2: Switch looks nice but it takes a bit more space so simple logo is better unless you find a way to make it take less space

## The lead, 2026-10-29 01:18

> I've made the switch compact: it now stands upright in the same small square as the Pause button. The mock-up shows it beside the simple icon at exactly the same size, and the revised ticket passes its pre-flight check.
>
> 1. **A switch that takes no more room than the icon**: I turned the switch upright: moon on top, sun below, the yellow knob over the theme that's on. The button is the same 36 px square as the Pause button (44 px on a phone), so it takes exactly the same room as the simple icon, and less than the word "Light" takes today. Both are in the mock-up at the same size, as A and B.
>    Action: Mock-up revised; ticket f69-07 builds A
> 2. **Why I still prefer the switch**: Now that the space is the same, the only difference is meaning. The single icon shows the theme you'd switch to, so the night page shows a sun, which can read as "it's day now". The switch shows both and which one is on, so it can't be read backwards. I recommend A. If you'd rather have B, the simple icon, say "B" and I'll change the ticket; nothing else changes.
>    Action: Ticket written for A
> 3. **When it gets built**: F69, I want a button to switch from light to night theme, is at priority 100, behind about 72 ready tickets. At about 18 minutes per ticket, that's roughly a day of factory work, unless you drag the card up the board.
>    Action: Nothing
>
> Proposals:
> - F69: the theme switch in the top bar (mockup)
> - F69: the button becomes a compact moon-and-sun switch (plan)
