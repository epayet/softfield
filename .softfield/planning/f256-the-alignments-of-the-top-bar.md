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

## The lead, 2026-11-17 20:28

> Approved by the owner on 2026-11-17: approved plan/f256: queued f256-01-top-row-in-line; F256 goes last on the board

## The owner, 2026-11-24 08:06

> the components are algined but text is still not really. job xx min on hour + project and the projection selection box text, are all over the place on desktop

## The lead, 2026-11-24 08:32

> I found why the words still sit at different heights, and drafted one more small developer ticket. The mock-up is `.softfield/cards/f256-mockup/text-line.html`; its plates are also drawn at twice the size so the difference is easy to see.
>
> 1. **Why the words are still off**: You're right. f256-01 lined up the boxes, but a box centres its text by the text's line height, which includes room for accents above and tails below. The labels (JOB, ON, PROJECT), the status words and the logo use the display font. The times use the mono font. The two fonts leave different room, so inside the same plate "JOB" and "0 min", or "ON" and "10 h 25 min", sit at different heights. The project's name is worse: the browser draws it inside the dropdown, with its own padding and arrow and a 13 px font no other plate uses. The host 127.0.0.1 is placed a third way.
>    Action: Fixed by f256-02 below.
> 2. **The fix: centre each word by its capitals**: Every word in the top row is trimmed to its capitals and its baseline before it is centred, with the CSS rule `text-box: trim-both cap alphabetic`. That covers the logo's name, the host, the status words and each plate's label and value. The middle of every word's capitals then sits on the same line, whatever the font. The Job, On and Project plates also become one shared style, where today each is its own copy. The mock-up draws Today and Proposed side by side, with the row's centre line drawn in.
>    Action: One developer ticket, f256-02-words-on-one-line. Its test measures each word's capitals on the real page, in both themes.
> 3. **The project's name becomes the plate's own text**: We can't place the text the browser draws inside a dropdown. So the plate shows the project's name itself, with a drawn ▾, and the real dropdown lies unseen over the whole plate. A click anywhere on it still opens the browser's own list, and the keyboard and screen readers work as before. The cost is one more layer in the picker to keep in mind. The plate shows the focus ring itself, and the test checks the click and the reload.
>    Action: Part of f256-02.
> 4. **Which browser do you use on the desktop?**: Chrome, Edge and Safari support the capital-trimming rule. Firefox doesn't yet, and there the row stays as it is now, no worse. If you use Firefox, the other option is to set a small pixel nudge for each font by hand. I'd avoid that: it breaks whenever a font or size changes. If the mock-up opens with a yellow note saying your browser can't trim, you're on one that doesn't.
>    Action: Recommended: f256-02 as drafted. If you're on Firefox, tell me and I'll add the per-font nudge for it.
>
> Proposals:
> - F256 round 2: the top bar's words on one line (plan)
> - F256 mock-up: the top bar's words on one line (mockup)
