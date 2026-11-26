# Milestone F299: A card says when the factory suggested it, and who: a review, the lead, a page

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-25.

## Notes
I want to be able to diffentiate whether a plant came from me, or from a suggestion from the factory, ie from a review

## What we know (2026-11-25)
- Every plant becomes a card through `_plant` (`runner/requests.py`), whose header always says "Planted by the owner on …", whoever wrote the words. A general-thread seed only adds "from the general thread's p3".
- A review's "What next" idea is planted from its plate (`idea_vals`, `factory_dashboard/milestones.py`): the request's value already carries `"from": "f286/3"`, but the runner ignores it; the only trace on the card is " From F286's review." glued to the end of the note. The review writes its ideas "in the owner's plant-note voice" (`runner/prompts.py`, section 6), on purpose.
- The Projects page's "Plant a card to fix it" and "Plant a card for a stack" (`stacks_routes.plant_value`) plant factory-written words with no mark at all.
- Nine cards carry the review tail today: F258, F260, F269, F270, F271, F292, F295, F296, F304. F201 and F202 say "From docs/backlog.md (fN-review), written by the lead". Two are suggestions the owner pasted and reworded by hand: F294 (from F273's review) and F303 (from F290's review).
- The board, the card page ("Your note") and the thread ("Your note") show every note as the owner's.

## Settled with the owner
- 2026-11-25: the origin is metadata on the card with a few fixed values (owner, review, …), never guessed from the note's words, and the card also says whether the owner edited a suggestion before planting it. Editing a suggestion before planting is F302's.

## Outcome
Every new card says where its idea came from (the owner, a review, the lead, the Projects page) and whether the owner edited it, as fields in its header; the board, its page and its thread show a factory suggestion as one, and the owner's own cards look as they do today.

## Done when
- a Plant box note gives a card whose header line reads `> **State:** idea · **Area:** factory · **Origin:** owner`
- planting F286's review idea from its plate gives `… · **Origin:** review · **From:** F286 · **Edited:** no`, and Notes that are the review's sentence without "From F286's review."
- a plant whose value says `edited: true` gives `**Edited:** yes`; an approved general-thread seed gives `**Origin:** lead`; a Projects page plant gives `**Origin:** projects`
- on the board, F296 and F292 carry an "F286 review" / "F97 review" tag beside their key, F303 "F290 review · edited"; F293, F297 and F298 carry none
- F296's page and thread say "F286's review suggested" where they said "Your note", with a link to F286's review; F303's add "edited by you"; F293's still say "Your note"
- the thirteen cards in "What we know" carry the fields on main

## Decisions
- **D1. Three header fields.** On the card's first header line, after `**Area:**`, as `**Fast lane:**` sits: `**Origin:**` is one of `owner`, `review`, `lead`, `projects`; for `review`, `**From:**` names the reviewed card's short key (`F286`); for any origin but `owner`, `**Edited:**` is `yes` or `no`. A card with no `**Origin:**` (every card older than this one) reads as `owner`. No table, no column: the doc is the card's record, and a merge keeps the kept card's header. The "Planted by the owner on …" line stays as it is: it says who pressed the button and when.
- **D2. The values come from the request, never from the words.** `planner.seed_card` takes the origin and writes the fields. `_plant` reads the plant value: `from: "fN/k"` → review, From FN; `from: "projects"` (new, sent by `stacks_routes.plant_value`) → projects; a general-thread seed (a plant with a `subject`) → lead; no `from` → owner. `edited: true` in the value → Edited yes. An unknown `from` plants as `owner`: never refused.
- **D3. One reader.** `runner/milestone.py` `Card` gains `origin: str = "owner"`, `origin_from: str = ""` and `edited: bool = False`, read beside `CARD_RESERVE_RE`. The board, the card page and the thread read them through `milestone.card`; nothing else parses the header.
- **D4. What it shows** (the picture: `.softfield/cards/f299-mockup/suggested-by.html`): a `card-suggested` tag in the board card's meta line, after the key, with a small cog and the source's short form ("F286 review", "lead", "Projects page"), and " · edited" when Edited is yes; drawn with a new `--suggested` token set to `--ink-2` in both themes, dashed border, never a status colour. On the card page and the thread, the "Your note" label becomes "<who> suggested", with "a factory suggestion · you planted it on <date>" (", edited by you" when edited) and, for a review, a link to that card's review (`/milestones/<full key>#review`). Owner cards are unchanged: no tag means yours.
- **D5. What it removes:** the " From FN's review." tail `idea_vals` adds to the text (the plate's planted state is found by `from`, not the text), and the "from the general thread's pN" note `_seed` adds. The backfill sets the fields on the thirteen cards, strips the tail from their Notes and drops F201's and F202's "From docs/backlog.md" line, in the same ticket.
- **D6. Lead, then developer.** The header, the request values and the backfill touch `runner/` and `.softfield/cards/` (protected): f299-01, lead. The three pages follow the mock-up and the `card-growing` tag: f299-02, developer.
- **Joint with F302, Edit a review's idea in its own plate before planting it:** this card reads `edited: true` from the plant value; F302's edit box sends it when the owner's text differs from the idea's. Until F302 is built, a plate plant is always `Edited: no`. F302 goes after this card.
- **Joint with F297, Projects page plant buttons also ask the lead:** both change `stacks_routes.plant_value`; F297 adds `ask`, this card adds `from`. Whichever lands second keeps the other's key.

## Before and after
- `/board`
- `/milestones/f296-show-each-milestone-s-net-code`
- `/planning/f296`
- `/milestones/f303-from-a-factory-suggestion-add-a`
- `/milestones/f293-a-lot-of-conversation-points-are`

## Tickets
- f299-01-plant-says-who-suggested (lead)
- f299-02-suggested-tag-on-the-pages (developer)
