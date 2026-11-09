# Milestone F230: Queue rows squeezed into the number column, one word per line

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-06.

## Notes
Cards in the queue wrap words weirdly, 1 word per line like 
Fast
 lane 
goes 
before 
everything

On mobile at least

## Why it happens
The Queue's rows (`.belt li` in `factory_dashboard/static/dashboard.css`) are a grid of two columns: 28px for the ticket's number, then the text. The fast lane's label row has no number, so its text lands in the 28px column and wraps one word per line, on every screen (a phone only makes it easier to see). Queued jobs (Planning, Plant, …) have no number either and are squeezed the same way. It came with `f81-12-fix-readout-units-and-belt-markup` (local model), which turned the fast lane's bay into plain list rows to fix invalid markup: the bay's CSS (`.lane-bay`) was left behind, unused, so the stripe and the label's look went too.

## Decisions
- **D1:** a Queue row without a number spans both columns; rows with one keep the 28px column.
- **D2:** the fast lane's rows get back the bay's look (the hazard stripe on the left, the label's type) on the list rows themselves; the dead `.lane-bay` rules go.
- **D3:** no mock-up: this restores the look F172 D9 already drew.

## Tickets
- `f230-01-queue-rows-full-width` (developer)
