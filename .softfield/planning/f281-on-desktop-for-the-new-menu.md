# F281: Every page in one row on a wide screen, no More

The planning thread behind F281's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-20 22:55

> on desktop for the new menu, there's more space so the fold of more is not needed, could just have all the buttons pages in one row

## The owner, 2026-11-21 05:04

> Perhaps this could be dynamic based on screen size. First 3 as re hard coded, and then the others as much as the screen fits and when it doesn't, show the more drop-down

## The lead, 2026-11-23 22:17

> I've drafted a mock-up with Laptop and Narrow window views, the card's Decisions and one developer ticket. The ticket passes pre-flight.
>
> 1. **Yes: on a wide screen More only costs a click**: The code agrees with you. F194 (The menu: Overview, Planning, Board in fixed places, the rest in a sub menu) gave its four slots fixed widths at every screen size. On a laptop they take about 490 px of a 1250 px row, and the other seven pages still sit behind More. All ten fit in one row of fixed widths, about 1030 px. Because the widths are fixed, F194's promise still holds: no slot moves from page to page or when the Planning count grows.
>    Action: Ticket f281-01: from 1100 px up, all ten slots in one row and no More.
> 2. **Where the change starts: 1100 px, not any desktop**: A laptop window at half-screen, about 640 to 1100 px wide, has no room for ten slots. Those windows keep F194's four slots and More, and so does the phone. The catch: the menu changes shape when you resize past 1100 px. The other choice is to let the ten slots wrap onto two lines, but then slots move, which is the problem F194 fixed. I recommend the fixed switch at 1100 px.
>    Action: Card decisions D2 and D4; the mock-up's 'Narrow window' picture shows it.
> 3. **Keep the main three looking like the main three**: With ten slots the same size, Overview, Planning and Board stop standing out, and you told F194 those are the three you use. I put a narrow hazard-stripe divider after Board and set the other seven a little smaller. Their short descriptions from the sub menu show when you hover. If you'd rather have ten equal slots, say so and the divider goes.
>    Action: Card decision D1; drawn in the mock-up.
> 4. **A developer builds it after F194's ticket, which the lead had to finish**: This is one template and one CSS change, with an example to follow, so it goes to a developer. The risk is the tests: F194's slot tests run at 1280 px, so at that width they will now see ten slots. The ticket says which tests to move to a 1000 px window and what to add at 1280 px. F194's ticket failed three times on its tests before the lead finished it, so that guidance is spelled out in full.
>    Action: f281-01: developer, difficulty 2, nothing to wait for.
>
> Proposals:
> - Every page in one row on a wide screen (mockup)
> - F281: one row on a wide screen (plan)

## The lead, 2026-11-23 22:25

> I've reworked the plan, the mock-up and ticket f281-01 so the row fits as many pages as the window allows; the ticket passes pre-flight. In the mock-up, drag the width slider to watch pages move between the row and More.
>
> 1. **Agreed: fill the row by width, and More holds the rest**: Overview, Planning and Board always come first. A narrow striped divider follows, then as many of the other seven pages as the window fits, in the sub menu's order (Projects, Tickets, Jobs, Runs, Timeline, Agents, Bench). More lists only the pages left over. When all seven fit, More goes. This is better than my first draft, which switched all at once at 1100 px and left a 1000 px window with only four slots.
>    Action: The mock-up and ticket f281-01 now do this.
> 2. **Do it with fixed steps in CSS, not a script that measures the bar**: Every slot has a fixed width, so we know in advance at what window width each page fits: Projects at 650 px, Tickets at 750, Jobs at 830, Runs at 900, Timeline at 1010, and all seven at 1070. Agents and Bench arrive together because once More goes there is room for both. A script that measures the bar would have to run after the page shows, so the row would visibly reshuffle on every page load and whenever the Planning count changes, which is the jumping F194 fixed. With fixed steps, each window width has exactly one layout, and going from page to page never moves a slot. The cost: if a slot's width changes later, its step has to change with it. The ticket's tests check every step for overflow.
>    Action: Card decisions D2 and D4.
> 3. **More still says where you are**: If the page you're on is in the row, its own slot turns yellow. If it's in More, More turns yellow and shows that page's name, as F194 does today. Example: Timeline at 900 px shows "Timeline ▾" in yellow. At 1280 px Timeline has its own slot.
>    Action: Card decision D3; try it in the mock-up with "You are on".
> 4. **Still one developer ticket, now difficulty 3**: The same three files, plus the six width steps and their tests. It follows the example of F194's menu, so it goes to a developer. Nothing has to run before it.
>    Action: f281-01, developer, difficulty 3.
>
> Proposals:
> - As many pages in the row as the screen fits (mockup)
> - F281: as many pages in the row as fit, More for the rest (plan)
