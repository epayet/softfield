# Milestone F227: Remove the 'Reorder on the board' link from the Overview's queue

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-05.

## Notes
The reorder from the board link in overview is unnecessary

## Plan
Mock-up: [`f227-mockup/queue-link.html`](f227-mockup/queue-link.html).
- **D1 The link goes:** "Reorder on the board ›" leaves the Overview's Queue panel, on the page and on its live refresh. It reverses the link F15 (Reprioritising tickets) added when the arrows went (f15-07); the Board tab, always in the page's tabs and carrying the project, is the way to the board.
- **D2 No empty heading:** with no job, no ticket and no review waiting, the panel says "The queue is empty." alone: "Next in line" and its list are left out.
- **D3 What doesn't change:** the rest of the list and the Board tab. f81-12 (the list's markup) still applies; its Context mentions the link, which it will simply no longer find if this merges first.

| # | Ticket | Who | Difficulty | Waits for | What |
|---|---|---|---|---|---|
| 01 | no-board-link-in-queue | developer | 1 | – | remove the link and the empty heading; the tests check both |

## Before and after
- `/`
