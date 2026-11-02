# F81: Bring the factory theme to the older pages, the Planning room first

The planning thread behind F81's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:27

> Some of it was designed with arknight in mind some not. Let's assess current state and improve

## The lead, 2026-10-26 23:30

> I assessed the dashboard against the factory theme, drew a mock-up (Today against Proposed, with a calmer variant) and drafted a 7-ticket plan on `plan/f81`. All seven tickets pass the ticket checks.
>
> 1. **Where the theme stands today**: Already themed: the top bar, the floor, the board, the reserve lever, the set-aside plate (F159, A set-aside ticket's page), the card page's "What it's about" (F158, A card says what it's about) and the Projects page. Still plain: the panel that every other page is built from (Overview, Tickets, Jobs, Runs, Timeline, Agents, Bench). It is a flat box with a title, with no plate header and no corner ticks. The tags, the crate card and empty panels have rounded corners. The Queue panel's title doesn't match the others.
>    Action: The assessment is written into the card's doc; tickets 01, 02 and 06 cover the plain parts.
> 2. **The Planning room can't be restyled as it is**: The Planning room, a card's thread and a proposal's page set their look line by line inside the page itself: about 210 of these settings across the three pages. Nothing changed in the stylesheet reaches them, which is why they look the plainest even though they are the pages you use most. Every new desk ticket adds more. So the real work is moving those settings into the stylesheet first. The theming itself is then small.
>    Action: Tickets 04 (Planning room) and 05 (thread and proposal) move them into the stylesheet with no change to behaviour. Ticket 07 adds a test so they don't creep back, and a line in the developers' notes.
> 3. **One change themes most pages at once**: Every panel gets the plate header that "What it's about" already has: a darker strip with the title, the hazard stripe filling the gap, and the source note in mono on the right. Each panel also gets corner ticks, and the page gets a faint grid behind it. "Needs you" becomes the one yellow plate. This changes only the stylesheet, so every page using panels gets it at once. Buttons become two kinds: a yellow Go button with a cut corner, and an outlined Plain button. Numbers become readouts, and Next in line becomes a row of crates edged in the floor's lead orange or developer blue.
>    Action: Look at the mock-up and say what to tone down.
> 4. **I'm leaving out the game's decorative codes**: Much of that game's look comes from serial numbers, code-like captions and labels that are only decoration. That clashes with your rule that every word and mark on a page says something. So the plates carry only the panel's own title, and the ornament (ticks, stripes, grid) uses ink and the hazard stripe only, never a colour that means something, and never moves. The mood comes from shapes, not from fake text.
>    Action: Written as D3 and D4 in the card's decisions.
> 5. **Keep F81 after the desk work on the board**: 26 ready tickets change these same pages, among them F132 (The overview shows the whole factory), F42 (The space for me to scroll), F73 (Set aside a ticket), F26 (Numbers next to the desk's groups) and F63 (The desk's order). If F81 runs first, those tickets add new inline settings to markup that has just been cleaned up, and their work has to be redone. F81 sits at the bottom of the board today, which is the right place: it themes those pages in their final form.
>    Action: No dependencies added; the board's order is enough. Move F81 up only if you'd rather see the look sooner and accept some rework.
> 6. **A calmer variant, if the bold one is too much**: The Proposed side has a checkbox for a calmer version: no grid, no stripe in the headers and square buttons with no cut corner. Everything else stays the same.
>    Action: Pick bold or calmer, or name the pieces to drop. I'll revise the mock-up and tickets 01 and 03 in the same reply.
> 7. **The light theme**: The mock-up shows the night theme only. The new shapes all use the existing colour settings, which already have light versions, so the pale floor gets the same plates and ticks. Every ticket's checklist asks for both themes, and the card's checklist ends with your phone check in both.
>    Action: Nothing for you now; check both themes when the work is in.
> 8. **Size and who builds it**: 7 tickets: 6 small developer tickets that follow the existing "What it's about" panel, and one small lead ticket for the test and the note. That is about 4 hours of line time at the recent median of 32 minutes a ticket. No ready ticket changes, so there's no need to pause the factory.
>    Action: Approve the plan to queue them.
>
> Proposals:
> - The theme reaches the older pages: Overview and Planning desk, Today and Proposed (mockup)
> - F81: themes the older pages, the Planning room first (plan)
