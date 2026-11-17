# F256: The top bar on a wide screen: every part on one line, one height, edges matched

The planning thread behind F256's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-17 09:03

> the alignments of the top bar on desktop is very wonky, nothing is aligned. from the logo to the night/light switches

## The lead, 2026-11-17 12:14

> I drew the top bar as it is today next to the fix, and drafted one developer ticket. The mock-up is `.softfield/cards/f256-mockup/top-bar.html`.
>
> 1. **Why nothing lines up**: You're right, and it comes from one rule. The top row lines its parts up on the bottom of their text, but only some parts follow that. The status is centred. The logo is centred in its own 44 px box. The word "Project" and its list sit on their text line. The night/light switch has no text, so its bottom edge goes on that line and it sits too high. On top of that there are five different heights side by side (44, 36, 36, about 24 and 24 px). The switch also stops 6 px short of the stripe's right end, and the logo starts 2 px in from its left end. Between 640 and about 1000 px wide, the row breaks onto two lines.
>    Action: Fixed by the plan below.
> 2. **The fix: one centre line, one height, matched edges**: Every part of the top row sits on the same centre line, from the logo to the switch. The pause sign, the "On" plate, the project picker and the switch are all 36 px tall, so their tops and bottoms line up too. The logo starts where the stripe and the tabs start, and the switch ends where the stripe ends. The mock-up shows Today and Proposed side by side at 1000 px and at 760 px, with guide lines drawn on.
>    Action: One developer ticket, f256-01-top-row-in-line. Its test measures the real page in both themes.
> 3. **The project picker becomes a plate**: Today the word "Project" floats beside a bare list. In the proposal it becomes a plate like the "On" one, with the same cut corner: a small "Project" label, then the project's name. This is the bolder version. If you'd rather keep just the word and the list, say so and I'll only line them up.
>    Action: Part of f256-01.
> 4. **A narrow window shortens the status words**: The row should never break onto two lines. So when the window is narrow, the status words ("Running: softfield · planner, job 2308") end in "…", and hovering the dot still shows the whole sentence. The cost is that what's running gets cut short on a half-width window. I think that beats a broken row, and nothing else on the row hides.
>    Action: Part of f256-01. Tell me if you'd rather hide the "On" plate first.
> 5. **It waits for the new menu**: Two tickets already in the queue change these same lines. f132-08 (F132, One view of the whole factory) moves the picker into the tabs. f194-01 (F194, The menu: Overview, Planning, Board in fixed places) puts it back in the top row. If f256-01 ran first, those two would undo most of it. My recommendation is to have it wait for f194-01. The catch is that f132-08 waits on lead work that is held by Claude's weekly allowance, so the fix may be a few days away. The other option is to run it now and have f194-01 keep the new picker plate when it puts the picker back, at the cost of reworking it once.
>    Action: Recommended: wait for f194-01, as drafted. Say "now" if you'd rather have it sooner.
> 6. **The phone's bar stays as it is**: Under 640 px the bar already centres everything on one line. The ticket keeps its 44 px buttons and its height, and only hides the new "Project" label, because there the list shows the project's name on its own.
>    Action: Nothing.
>
> Proposals:
> - F256: the top bar on a wide screen, in line (plan)
> - F256 mock-up: the top bar, in line (mockup)
