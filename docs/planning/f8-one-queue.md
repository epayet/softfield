# F8: one visible queue

The planning thread behind F8's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 07:45

> I like the switches but the labels take a bit of space on mobile. I also wonder how to make the button a bit more fun in the theme?

## The lead, 2026-10-09 07:47

> I drafted a phone mock-up of a factory lever and one developer ticket (f8-14). Both are on plan/f8 for you to look at.
>
> 1. **The labels on a phone**: Each switch is a sentence and a button on a line of their own, so on a phone each Claude meter takes two extra lines. I'd move the switch onto the meter's own line, next to the percent, with a two-word label: "use reserve". The full sentence ("Let the factory use the week's reserve") still gets said: in "How to read the allowance", in the lever's tooltip, and to a screen reader. On a phone that saves about two lines per meter.
>    Action: Ticket f8-14-reserve-lever, with the picture docs/milestones/f8-mockup/reserve-lever.html
> 2. **I'd keep a short label rather than none**: An icon-only lever would save one more word, but you asked that every mark say what it means, and both levers would look the same. "use reserve" is the shortest label that still says it.
>    Action: Nothing: built into f8-14
> 3. **Making it more fun, in the factory theme**: The button becomes a small machine lever. Its knob sits in a dark slot. When on, the slot turns into yellow-and-black hazard stripes, a lamp lights up, and the knob snaps across with a small bounce. When you've pulled it but the runner hasn't taken it yet, the knob waits halfway and the lamp blinks, inside the dashed orange edge you already know. I kept rubber ducks out: they're Mum's product theme, not the factory's. Open the mock-up on your phone and tap a lever to try it.
>    Action: Mock-up reserve-lever.html; tell me what to change before it's queued
> 4. **"on until …" takes the place of the mark's words while it's on**: To avoid adding a line, "on until Sat 09:30" shows in yellow where "reserve kept from 85%" usually is. The mark still shows on the bar, and its words are in its tooltip. The cost: while a lever is on, you don't see the mark's percentage in words.
>    Action: Nothing, unless you'd rather keep both (one more line)
> 5. **It waits for f9-28**: f9-28-allowance-live (ready) changes the same panel: it refreshes it live and moves the legend to the bottom. f8-14 depends on it so the two don't collide. f8-14 is small and follows the f8-06 example, so a developer builds it.
>    Action: Nothing: the dependency is in the ticket
>
> Proposals:
> - F8: the reserve switch becomes a lever (plan)
> - The reserve lever, today vs. proposed, on a phone (mockup)
