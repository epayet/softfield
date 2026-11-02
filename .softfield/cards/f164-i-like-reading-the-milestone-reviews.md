# Milestone F164: Plant a review's ideas straight from the review

> **State:** ready · **Priority:** 12 · **Area:** factory
> Planted by the owner on 2026-10-21.

## Notes
i like reading the milestone reviews and suggestions for the factory or the current project. whenever it suggests something, i want the option to plant it (ask lead or just plant) from there directly for the ideas i like

## What we know (2026-10-21)
- A review's suggestions sit in its sign-off sheet, mostly "6. What next" (Product, Factory), stored in `milestones.signoff` as `what_next` and shown as text on the milestone page (`factory_dashboard/templates/milestone.html`, `_to_html` in `factory_dashboard/milestones.py`). The card's thread shows only What changed, How to test and Decisions (`_SHEET`, `_review` in `factory_dashboard/planning.py`), then "The whole review".
- Three reviews already write their best idea as a quoted `> ` line ready to plant (F19, F28, F135); the page shows it as "&gt; …". The owner copied F19's by hand into the Plant box: it is F166. Lesson cards were planted the same way (F144, F145), and Travel companion's M1 review idea became F163 on Softfield's board.
- Other suggestions are plain bullets with no ready words (F19's "Checkpoints on template work…").
- A `plant` request's value is `{text, ask, area}` (`planner.planting`, `runner/planner.py`); unknown keys are ignored. Its result reads "planted .softfield/cards/<card>.md" once done.

## Outcome
Every idea a review suggests shows as a plate with Plant and Plant and ask the lead, on the card's thread and on its milestone page; pressing one shows it on its way at once, and once planted the plate links to the new card.

## Done when
- F19's thread shows "Ideas from this review · 1" with its Plans idea marked "Planted" and linking to F166, Plant and Plant and ask the lead gone
- F28's and F135's ideas show their two buttons; pressing Plant turns the plate dashed "On its way", and after the runner's pick it links to the new card, whose notes end "From F28's review."
- a factory idea from Travel companion's review plants on Softfield's board
- the next review writes each idea that needs a card as a quoted line under Product or Factory

## Decisions
- **D1. An idea is a quoted line.** The review writes every suggestion that needs a card as one `> ` line under its Product or Factory bullet in What next, in the owner's plant-note voice: one sentence, self-contained, naming the place and the change. What the review already did itself (a rule in `runner/instructions/lead.md`) is said in words, not quoted. A lesson or an unclog that needs a card is quoted in What next too. Only quoted lines get buttons: a plain bullet is the lead talking, not a note to plant.
- **D2. Reading the ideas.** `review_ideas(sheet, key)` in `factory_dashboard/milestones.py`: each line of any section of the stored sheet that starts with `>` after its indent, in section order then line order. Its id is `<short key>/<n>` (n from 1). Its area: product when the nearest bullet above it in its section starts with `**Product`, else factory. Its project: product → the review's own; factory → the factory's own project, the registered project whose `repo` holds `runner/loop.py` and `factory_dashboard/app.py`, else the review's own.
- **D3. An idea's state**, from the target project's `owner_requests` of kind `plant`, the latest that matches: `value.from` equals its id, or `value.text` starts with its text (whitespace collapsed, a final full stop ignored), so F166's hand-made plant counts. No match: the buttons. `done` NULL: on its way. Done with a result starting "planted ": Planted, linking `/planning/<the card's short key>`. Done otherwise: "Didn't go through: <result>" and the buttons again.
- **D4. The buttons post the Plant box's request**, `plant` with value `{text: "<idea>\n\nFrom F19's review.", ask, area, from: "<id>"}` and the target project. On press the plate turns dashed hazard, "On its way · planted at the runner's next pick", and its buttons go (Sign off's `hx-on::before-request` swap). Nothing changes in `runner/` or `factory_dashboard/requests.py`.
- **D5. Where they show.** The thread's "The review" gets "Ideas from this review · N" after its sections; the milestone page draws each quoted line in place as a plate instead of "&gt; …". Plate: the board's area colour on its left edge, corner ticks in the rules' ink, no new token. Mock-up: `.softfield/cards/f164-mockup/review-ideas.html`.
- **D6. Who builds.** 01 lead (`runner/prompts.py`, `runner/instructions/lead.md` are protected); 02 developer (Python and its tests, `_review` is the example); 03 lead: template-and-script work on these pages cost developers hours in F19 and F28, and both reviews ask for the lead to take it.

## Tickets
- f164-01-reviews-quote-their-ideas (lead)
- f164-02-review-ideas-and-their-state (developer)
- f164-03-idea-plates-with-plant (lead, after 02)
