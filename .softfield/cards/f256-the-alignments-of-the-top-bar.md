# Milestone F256: The top bar on a wide screen: every part on one line, one height, edges matched

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-17.

## Notes
the alignments of the top bar on desktop is very wonky, nothing is aligned. from the logo to the night/light switches

## Why it happens (from the code, 2026-11-17)
- `factory_dashboard/static/dashboard.css` line 92: `.bar-top { align-items: baseline }`. Only some parts line up on a text baseline: the status sets `align-self: center`, the brand centres itself in its own 44 px box, "Project" and its select sit on their text line, and the theme switch, which has no text, puts its bottom edge on that line, so it rides high.
- The row's controls come in five heights: the dot's button 44 px, the sign and the switch 36, the "On" plate (F251) about 24, the select about 24.
- The switch's 24 px plate sits in a 36 px button, so it ends 6 px short of the stripe's right end; the logo's crate starts 2 px in from the stripe's left end.
- Between 640 px and about 1000 px the row wraps (`flex-wrap: wrap`) onto two lines.
- The phone's bar (under 640 px) is a grid with `align-items: center` and lines up already.

## Expected outcome
On a wide screen the top row reads as one line: every part is centred on the same line, every control is the same height, the left edge of the logo meets the stripe's and the tabs', and the switch ends where the stripe ends. A narrower window shortens the status words with "…" instead of breaking the row in two. The phone's bar doesn't change.

Picture: `.softfield/cards/f256-mockup/top-bar.html` (Today against Proposed, real values of 2026-11-17).

**Done when:** f256-01 is merged. To test, on the desktop: open the Overview; the logo, the dot, the words, ⏸, the "On" plate, the project picker and the switch sit on one line with tops and bottoms matching; narrow the window to about 760 px and the row stays one line, the words ending in "…". Then flip to the light theme: the same.

## Decisions
- **D1. One centre line, one height.** From 640 px up, `.bar-top` is one row that never wraps, centred (`align-items: center`). The sign, the "On" plate, the picker and the switch are all `--control-h` (36 px, a new token at the top of `dashboard.css`); the dot's button keeps its 44 px tap.
- **D2. The picker is a plate** drawn like the "On" plate: a `.key` "Project", then the select without its own border, in one bordered plate with the `--notch` cut. `base.html` wraps the word in `<span class="key">`; the `select`'s `name`, `onchange` and the `<noscript>` button stay. On a phone the key hides (the select names the project, as today).
- **D3. The edges.** The brand takes back the crate's 2 px inset, so its left edge meets the stripe's and the tabs'; the switch is as wide as its plate on a wide screen, so its right edge meets the stripe's end. The phone keeps its 44 px switch.
- **D4. Narrow windows squeeze the words.** The status words don't wrap: they end in "…", and the dot's `title` already holds the whole sentence. Nothing else hides.
- **D5. After F194.** f256-01 waits for f194-01 (F194, The menu: Overview, Planning, Board in fixed places), which puts the picker back in `.bar-top` after f132-08 (F132, One view of the whole factory) moved it into the tabs; all three change the same lines of `base.html` and `dashboard.css`.

## Before and after
- `/`
- `/planning`

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | top-row-in-line | D | 2 | f194-01 | D1 to D4 |
