# Milestone F291: The project picker's open list reads grey on white in the dark theme

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-24.

## Notes
the project picker list textbox is grey on white, hard to read. where does that come from

## Cause
`factory_dashboard/static/dashboard.css`, rule `.bar-top .filters select`, added by f256-01 (F256, the alignments of the top bar): `background: transparent` lets the label's plate show through the closed picker, but the browser draws the opened list on the select's own background, and a transparent one falls back to white. The text stays the dark theme's ink, a light grey (#dfe4e8): grey on white. The light theme's dark ink on white reads fine.

## Plan
One developer ticket, f291-01-picker-list-readable: the select's background becomes `var(--plate)` (the label is already that colour, so the closed picker looks the same) and its options get `var(--plate)` and `var(--fg)`. No mock-up: it restores the look the picker already meant.
