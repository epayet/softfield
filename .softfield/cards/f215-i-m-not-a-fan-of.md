# Milestone F215: A plain floor: the grid comes off the dashboard's background

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-04.

## Notes
I'm not a fan of the grid like background

## Expected outcome
Every dashboard page sits on a plain floor, in both themes: the lines every 32 px are gone from the background, and the plates, ticks, stripes and belts stay as they are. New work doesn't bring the grid back, because the theme rule no longer lists it.

The picture: [`f215-mockup/floor.html`](f215-mockup/floor.html) (Today against Proposed).

## Done when
- No page shows the lines, night or light, on a phone or a wide screen.
- Nothing else on a page changes: table rows, bars and other hairlines drawn in `--grid` look as they did.
- The theme rule in `runner/instructions/author/owner.md` no longer names a grid.

## Before and after
- `/`
- `/planning`
- `/tickets`

## Decisions
- **D1 The body keeps its colour and loses its background image.** Only the grid's declarations in `body` of `factory_dashboard/static/dashboard.css` go (`background-image` with its two gradients, `background-size`).
- **D2 The `--grid` token stays, under its name.** Other rules use it as the colour of a hairline or an empty bar, not as a grid; renaming them is churn with nothing to see.
- **D3 Other patterns stay:** the board's diagonal hatch (`.plots`) and the `--ghost` stripes are a different look and weren't the owner's note.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | floor-without-grid | D | 1 | – | D1, and the test that held the grid now holds its absence |
| 02 | theme-rule-without-grid | lead | 1 | 01 | the theme rule and F81's D3 stop naming the grid |
