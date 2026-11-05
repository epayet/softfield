# F199: The factory floor: a small strip on the Overview and a one-screen map

The planning thread behind F199's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-02 17:43

> Let's improve the factory floor it's not very good ATM and a bit too big on mobile especially. Planted rows is not super helpful. Remember arknight Endfield for inspiration. Eventually I'll want an android widget to be able to see quickly what's going on ATM, and an embedded version of the factory to include in my website. I wonder if a small version and a full screen version where you can see all the components from a glance a bit like a map be cool, open to ideas

## The lead, 2026-11-02 23:23

> Drafted a small strip for the Overview and a one-screen map as its own page, plus the mock-up, five tickets and two seeds. Pre-flight passes, but I couldn't open the mock-up in a browser from this job.
>
> 1. **A small version and a full-screen map: yes**: Your idea is the right shape. The small one is a strip on the Overview: one belt, six stops (Planted, Queue, the machines, Checks, Merged today, Ripe) and one line saying what runs. The full one is a map at /floor: the whole factory from above, on one screen with no scrolling, and a Full screen button. Tapping the strip opens the map.
>    Action: Tickets f199-01 (map) and f199-02 (strip); the picture is in the mock-up.
> 2. **Too big on a phone**: Today's phone floor is about 1,900 px tall on a 390 px phone, so 2 to 3 screens. The strip is about 170 px. The upright map fits one screen, because it keeps only short words and big numbers, and a tap gives the rest.
>    Action: Tickets f199-02 and f199-01 test those sizes in a browser.
> 3. **Why Planted rows don't help**: They show the first four cards by number, not by the board's order. On 2 Nov they showed Bugs, F9, F10 and F25 out of 57 planted, while the line's next cards were F170, F187 and F85. Instead, every planted card becomes one small tile in the board's order: the yellow fill is its merged tickets, and an orange edge means a ticket has started. A tap on the plot lists the cards as links.
>    Action: Tiles in f199-01, the list in f199-04.
> 4. **The look you asked for**: What I took from the game you named is its top-down factory planner: a grid seen from above, machines as footprints, straight belts with square corners, and angular plates with hazard stripes. All of it is our own SVG on the existing tokens, with no new colour, and nothing is copied or named on the page. 'Waiting for Claude' is in the mock-up too, as a sign on the machine and in the top line.
>    Action: Press the moment buttons and tap things in the mock-up, then tell me what to tone down.
> 5. **Other shapes I looked at**: One big drawing you pinch and pan is the usual map idea, but fitted to a phone its text is unreadable, and its gestures fight with tapping. A 3D-style angled view would look the boldest, but every machine becomes artwork to draw and to keep up as agents change. I recommend the flat grid now. An angled look could come later without changing the data.
>    Action: Nothing, unless you want one of these instead.
> 6. **The hidden cost: this is a rebuild**: Two sizes drawn the current way would make four sets of hand-placed coordinates. So I replace them with two tables on a 20-unit grid and one drawing function. That removes the current drawings, and many of the browser tests in test_line.py are about them. So it takes two lead tickets (f199-01, f199-03), not polish. I think it's worth it, because the strip then needs no drawing code at all.
>    Action: Tickets f199-01 and f199-03; the strip and the two small tickets go to developers.
> 7. **Belts lose their words**: Words on 13 belts are what collide today, and they would never fit the phone map. Belts keep only today's number; the words come on a tap and in the key. The risk is that a new reader can't tell a belt's meaning at a glance. You know the floor, so I'd accept that.
>    Action: Tickets f199-01 and f199-04. If you miss them, I can keep words on the wide map only.
> 8. **Replay moves to the map**: The Replay bar leaves the Overview, which shortens that page. Its choice of stretch also drives While you were away, so that panel gets its own select and keeps working in place. This changes where f9-26 put Replay, right under the floor.
>    Action: Ticket f199-03.
> 9. **Android widget: possible, but not live**: Android refreshes home-screen widgets on a schedule of about 15 to 30 minutes unless an app runs constantly in the background, so it won't update every 5 seconds. It also can't reach the dashboard away from home, since the dashboard stays on your Wi-Fi (ADR 26). Before building an app, I'd try a ready-made widget app that reads a small JSON address; I haven't tested one here. That shows cheaply whether you really look at it. The strip's data (f199-02) is the only preparation it needs.
>    Action: A seed with these questions, nothing built now.
> 10. **Website version: it can't simply be embedded**: Your visitors can't reach a dashboard that lives on your home Wi-Fi, and it shouldn't be opened up for them. So the factory would have to publish a small file to your website every few minutes. That means what goes out needs deciding: titles carry your notes and your Mum's product. I recommend counts and machine states only, which is why the strip's data holds no titles. It needs an ADR from you before it's built.
>    Action: A seed with these questions; the ADR comes when you plan it.
> 11. **After approving, drag F199 above F9**: An approved card lands at the bottom of Planted. If it stays there, F9, Line polish, runs f9-27 first, a paid lead ticket that reworks the Planted rows this card removes. F10, Crates on the belts, would also build its crate motion on the old drawing. Dragging F199 above F9 avoids both, and f199-01 then sets f9-27 aside. F199 still waits for f132-05 from F132, One view of the whole factory, because both change the same drawing code.
>    Action: Your drag on the board, once approved. No other change is needed.
> 12. **The mock-up hasn't been seen on screen**: This job can't open a browser, so I checked the drawing's sizes and positions by reading the code. Today runs a copy of the live drawing code on the real values, cut down for the frame. If something overlaps or looks wrong, it's a mock-up slip, not a design choice.
>    Action: Tell me what looks off and I'll fix it and the tickets together.
>
> Proposals:
> - F199 mock-up: the floor as a strip and a map (mockup)
> - F199: the floor as a strip and a map (plan)
> - An Android widget showing what the factory is doing (seed)
> - The factory strip on my website (seed)
