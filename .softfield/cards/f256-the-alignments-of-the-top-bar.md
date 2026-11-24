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

## Round 2: the words (owner, 2026-11-24)
"the components are aligned but text is still not really. job xx min on hour + project and the projection selection box text, are all over the place on desktop"

**Why (from the code, 2026-11-24):** f256-01 centred the boxes, and a box centres its text by its line box, which holds room for accents above and tails below. Chakra Petch (keys, status words, logo) and JetBrains Mono (times) leave different room, so in the same plate "JOB" and "14 min", or "ON" and "10 h 25 min", sit at different heights. The `.uptime`, `.job` and picker plates are three copies of one style, the picker's value in a 13 px display type the others don't use. The project's name is drawn by the browser inside the select, with its own padding and arrow, out of the stylesheet's reach. The host tag places its text a third way (a 20 px line in 22 px).

Picture: `.softfield/cards/f256-mockup/text-line.html` (Today against Proposed, real values of 2026-11-24, with the plates at twice the size).

**Done when:** f256-02 is merged. To test, on the desktop at full width: the capitals of "SoftField", the host, the status words, "JOB", its time, "ON", its time, "PROJECT" and the project's name all have their middle on one line; pick another project from the plate and the page reloads with it. Then the light theme: the same.

- **D6. Words centred by their capitals.** Every text in the top row (the brand's name, the host, the status words, each plate's key and value) gets `text-box: trim-both cap alphabetic`, so centring its box centres its capitals. Chrome, Edge and Safari draw it; a browser without it (Firefox today) draws the row as f256-01 left it, never worse.
- **D7. One plate style.** `.tag` (a `.key` in 11 px display caps, a `.val` in 600 12 px mono) replaces the copies in `.uptime`, `.job` and the picker; `.uptime` and `.job` keep their own names for their margins and the phone's rules.
- **D8. The picker's name is the plate's own text.** The label holds the key, a `.val` with the project's name and a drawn caret, and the `select` laid over the whole plate at `opacity: 0`: a click anywhere opens the browser's list; `name`, `onchange`, the `<noscript>` button and keyboard use stay; the plate shows the focus ring (`:focus-within`). On a phone the key still hides and the `.val` names the project.

## Before and after
- `/`
- `/planning`

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | top-row-in-line | D | 2 | f194-01 | D1 to D4 |
| 02 | words-on-one-line | D | 2 | – | D6 to D8 |
