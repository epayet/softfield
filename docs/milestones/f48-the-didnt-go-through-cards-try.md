# Milestone F48: Try again plants a note, once

> **State:** ready · **Priority:** 2 · **Area:** factory
> Planted by the owner on 2026-10-08 as "the didnt go through cards try again don't work or dismiss".

## Notes
the didnt go through cards try again don't work or dismiss

### What the database showed (the lead, 2026-10-08)
- **Dismiss worked**, late: six dismisses (requests 27, 46, 50, 52, 60, 64) were applied as "dismissed request N", each at the runner's next pick, 20 to 35 minutes after the press.
- **Try again was refused again**, for a new reason: four retried plants got "`<slug>` is a card already: f35-…, f38-…, f41-…". Those notes had been planted in the meantime (F35, F38, F41), and `_plant` refuses any idea whose slug (its first six words) an existing card has. Each refusal is a new "Didn't go through" card with the same words, so a dismissed note came back as a fresh card: it looked as if neither button did anything.
- Two notes that only start alike (the same first six words) collide the same way, and F31 D7's one-box plant makes that likelier.

### From F46: the dismiss cards that didn't go through button doesn't seem to work (merged by the owner on 2026-10-08)
(none)

## Outcome
- **A taken name never refuses a note:** the same words again are "planted already" with a link to the card; other words get a card of their own.
- **One card per note:** Try again takes the refused card off the desk the moment the retry is sent; if the retry fails, its own card shows instead.

## Decisions
- **D1 A taken slug isn't a refusal (owner.md, 2026-10-08: "the owner's words are never refused unseen", don't refuse for form):** in `_plant`, when `card_named` finds the slug taken:
  - if that card's doc holds the note's words (title and thoughts, whitespace collapsed), nothing is written and the result is `planted already: docs/milestones/<stem>.md`, a worked result (it starts with `planted `), so it doesn't land on the desk;
  - otherwise the new card takes the slug with `-2` (then `-3`, …), and plants as usual. A real repeat is the lead's to merge (f6-12).
- **D2 Try again carries what it retries:** the Plant form and a thread's reply box get a hidden `again` (the refused request's id), filled by Try again and cleared after a send. The request's value carries it (`{"title", "thoughts", "ask", "again"}`, `{"text", "comments", "again"}`); the runner ignores it. The desk's "Didn't go through" leaves out a refused request that a later request's `again` names, pending or done: a retry that fails again shows as its own card, so there is one card per note. No new request kind, and `POST /requests` still writes one row.
- **D3 Dismiss stays as it is:** it hides the card at once and the runner records it at its next pick (ADR 18: the dashboard writes only request rows). No change.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | retry-plants-once | L | 5 | – | D1, D2 |

## Done when
- Plant a note whose first six words match a card's, with other words: a second card is planted (`…-2`), nothing on the desk.
- Try again a refused note that was planted since: the result says "planted already" with the card, and the desk shows nothing for it.
- Press Try again on a refused idea and send it: its card leaves the desk at once; a retry refused again shows one card, not two.

## Not here
- F31 D7 (one-box plant, f31-05) keeps D1: its slug rule is the same `_plant`.
