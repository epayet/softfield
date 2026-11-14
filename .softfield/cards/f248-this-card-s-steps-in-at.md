# Milestone F248: This card's steps at the top of the thread too, as on a proposal's page

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-14.

## Notes
'this card's steps' in at the top for proposals but bottom for conversations. As it's unified now make it at the top everywhere

## Expected outcome
"This card's steps" is in the same place on every page of a card: at the top, in the card's header, under its title. Picture: [`f248-mockup/steps-at-the-top.html`](f248-mockup/steps-at-the-top.html).

## Decisions
- **D1 The thread's strip goes in its header.** It changes F210 D3, which put it under the latest exchange, above the reply box. On the thread, `_partials/card_steps.html` and "Nothing becomes a ticket until you approve it." move into `header#card`, after the title and the merged links, as on a proposal's page. The partial doesn't change.
- **D2 It still changes on its own.** The strip leaves `#conversation`, so the page's redraws (the 5 s poll, the redraw after Send) also replace it from the page they fetched: "being revised", a new proposal and the not-sent marks show without a reload, as they do today.

## Tickets
| # | Ticket | Who | Difficulty | Depends on | Covers |
|---|---|---|---|---|---|
| 01 | steps-at-the-top-of-the-thread | developer | 3 | – | D1, D2 |

## Before and after
- `/planning/f241`
- `/planning/f207`
