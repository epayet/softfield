# F225: The night switch slides by itself when a page loads

The planning thread behind F225's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-05 11:03

> There is a tiny amount of time when the page loads where the night light switch moves from light to night with the orange slider animation which is annoying. Animation not needed on page load, only when changed

## The lead, 2026-11-05 11:22

> One small ticket drafted to stop the slide on load. Nothing is queued until you approve it.
>
> 1. **Why the switch slides on load**: Every page is drawn with the switch on the light side. The script only sets the real side once the page's other scripts have loaded, which can be after the first paint, so on the night theme the knob visibly slides across. The theme itself is right from the first paint: only the knob is late.
>    Action: Fixed by the ticket in the next point.
> 2. **The fix: the knob follows the theme**: The stylesheet will place the knob from the theme, which is already right before the first paint, instead of from the late setting. The knob then starts in the right place, so nothing moves on load. I recommend this over turning the animation off during load, which is what you asked for in effect: the knob would still start on the wrong side and jump across instead of sliding. It would also need more script.
>    Action: A small developer ticket, changing the stylesheet and the tests only.
> 3. **When it still slides**: It slides when you press the switch. It also slides when your system's theme changes, if you've never pressed the switch, because that's a real change too.
>    Action: The ticket's tests check that pressing still slides and loading doesn't. The system change uses the same rule and has no test of its own.
> 4. **No mock-up**: The switch looks the same in both themes: only the slide on load goes, so there's nothing new to draw.
>    Action: Tell me if you want one anyway.
> 5. **Its place on the board**: This card sits at the default place, 100, behind most of the 117 ready tickets, so at about 33 minutes each it could wait days. It's about the smallest ticket there is, and you see this on every page load.
>    Action: After approving, drag the card up the board if you want it sooner. I recommend it.
>
> Proposals:
> - The night switch stays still when a page loads (plan)
