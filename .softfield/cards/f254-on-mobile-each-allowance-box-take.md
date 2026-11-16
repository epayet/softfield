# Milestone F254: The allowance takes less height on a phone

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-16.

## Notes
On mobile each allowance box take a lot of vertical space for nothing

## Expected outcome
On a phone, the Overview's Agent allowance takes about 260px instead of about 420px for its three windows, with every word, colour and lever kept. A wide screen is unchanged.

Done when: at 390px wide, the three windows (Claude's 5-hour window, Claude's week, Copilot's month) stand at most 280px tall together, without the legend line.

To test: open the Overview on the phone and scroll to Agent allowance: each window is a row, not a box; its name, percent and meter sit beside the "use reserve" lever; the reset, read and mark words run on as one line under it, and "at this rate" keeps its own line.

## From the code (2026-11-16)
- The phone rules are under `@media (max-width: 639px)` in `factory_dashboard/static/dashboard.css` (f9-17): each window `#allowance > .allow > div` is a bordered box with padding, and keeps the wide screen's three blocks: a `.line` holding the name, the reading and the lever (44px tall, its touch size), the `.meter`, then a `.line` of `<small>`s laid out `space-between` with `flex-wrap`, so each small takes its own piece of a line and they wrap into two or three lines (`factory_dashboard/templates/_partials/allowance.html`).
- The partial is refreshed every 5 s through `/live` (`hx-select-oob="#allowance:innerHTML"`), so anything folded behind a tap would close again within 5 s.

## Decisions
- **D1. A phone-only change.** The CSS goes inside the existing `max-width: 639px` block; the wide screen looks as it does today. A template change is allowed only where the phone layout needs a wrapper (the name and reading together, for example), and it must leave the wide screen's look as it is.
- **D2. Nothing hidden.** Every word stays visible: no tap to unfold (the 5-second refresh would fold it again), no shortened labels. The lever keeps its 44px touch height; the name, reading and meter share that band instead of a line of their own.
- **D3. Rows, not boxes.** Windows are separated by a thin `--grid` rule, as rows are elsewhere; no border or background per window. The "Over pace" and "Last hours" plates and the Fast lane line stay as drawn.

Picture: [`.softfield/cards/f254-mockup/allowance-phone.html`](f254-mockup/allowance-phone.html).

## Before and after
- `/`

## Tickets
1. `f254-01-allowance-rows-on-a-phone` (developer): the phone layout of the allowance, as the mock-up's Proposed.
