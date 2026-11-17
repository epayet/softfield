# Milestone F261: A short review on the card's thread, with the whole review one tap away

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-17.

## Notes
The review notes on the planning sign off are a sub part of the whole review but it's a big part and when I look at the whole review I have to scroll down a lot. Keep the important info on planning conversation and then I can dig through the whole review

## What we know (2026-11-17)
- The thread draws the review between "Your note" and the conversation, every part open: What changed, How to test, Decisions waiting for you (`_SHEET` in `factory_dashboard/thread.py`, the `{% if review %}` section of `factory_dashboard/templates/thread.html`). F251's is about 1,900 characters, the lead's latest message comes under it.
- "Decisions waiting for you" says "None." on every one of the last 12 reviews.
- F216, A shorter, consistent review page (ready), D13 adds "Decisions made along the way" to the thread's review, which makes it longer. Its f216-03 builds that; this card's 02 replaces it after.

## Expected outcome
A card's thread shows its review in one short plate: what it does now in two lines, whether its Done when is met, what needs the owner, Sign off, and a link to the whole review saying what's there. How to test folds, one tap away. Picture: `.softfield/cards/f261-mockup/thread-review.html`.

**Done when:** on a phone, F251's thread shows its review in under half a screen with the folds closed; a review with a decision waiting shows it open; an old review with no "In short" shows the first sentence of What changed.

## Decisions
- **D1. A new sheet section, "In short",** first in the sheet (`### In short`, before `### 1. What changed`): at most two lines, what the card does now and whether it matches the plan and mock-up. In `REVIEW` (`runner/prompts.py`) and `runner/instructions/lead.md`'s "Sign-off sheet"; `SIGNOFF_SECTIONS` in `runner/milestone.py` gains `"In short": "in_short"`. It is the review's own words, the one thing on the plate it writes for the thread.
- **D2. The thread's review plate, in order** (replaces F216 D13): Needs your answer (only when `decisions` doesn't start "none", open); In short (the `.in-short` plate the lead's messages use); Done when, as of now (F216 D3) as a tally ("3 met · 1 your check · 1 not yet") with only the Your check and Not yet lines written out; How to test as a closed `<details>` whose summary gives its step count; Ideas from this review (F164) as a closed `<details>` with their count, when there are any; Sign off; then "The whole review ›" as a tap, its gist naming what the card's page holds (What changed, "n decisions made along the way", what it cost).
- **D3. Fallbacks for old reviews:** no `in_short`: the first sentence of `changed` (up to the first `. ` or line end, Markdown stripped). No `done_check`: no tally. Nothing new is stored for old cards.
- **D4. The counts are the page's own** (as F216 D9): steps are the numbered or bulleted items in `how_to_test`, decisions the bullets in `along_the_way`. The card's page (`/milestones/…`) doesn't change: the whole review stays as F216 draws it.
- **D5. Who builds:** 01 lead (protected `runner/`), after f216-01 which rewrites the same prompt lines. 02 developer: a template, `thread.py` and CSS, following the lead message's `.in-short` plate and the thread's existing folds; after f216-03, which touches the same lines.

## Before and after
- `/planning/f251`
- `/planning/f216`

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | review-writes-in-short | lead | 2 | f216-01 | D1 |
| 02 | thread-review-short-plate | developer | 3 | 01, f216-03 | D2, D3, D4 |
