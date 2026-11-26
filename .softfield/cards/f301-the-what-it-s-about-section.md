# Milestone F301: A reviewed card's page opens on What changed

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-25.

## Notes
the 'what it's about' section of revviews is not super helpful, i just skip straight to what changed

## What we know (2026-11-25)
- On a reviewed card's page (`factory_dashboard/templates/milestone.html`), "What it's about" sits between the head and What changed: the plan's "What it will do", then "Done when, as of now" (F216 D3). On F286's page it is about 230 words, so on a phone What changed starts below the first screen.
- Its two parts repeat the review: "What it will do" says again what What changed says, and every "Your check" line is a step in How to test too (F286: four of six lines).
- The one part nothing else says is a Done when line still **Not yet**: no review on main has one, but it is the line that matters when it comes.
- F261, A short review on the card's thread (ready), builds a Done when tally ("3 met · 1 your check · 1 not yet") for the thread in `factory_dashboard/thread.py` (f261-02), and leaves the card's page alone (its D4).
- The owner's rule "Expected against actual, first" (`runner/instructions/author/owner.md`) puts the expected outcome and Done when first on any milestone view; this card changes it for a reviewed card.

## Expected outcome
A reviewed card's page opens on What changed, straight under its head. What the card was meant to do is the first fold of Behind it, its gist the Done when tally, and a Done when line still "Not yet" heads What changed so it is never folded away. A card not reviewed yet shows "What it's about" as today. Picture: `.softfield/cards/f301-mockup/review-top.html`.

**Done when:** on a phone, F286's page shows What changed's first lines on the first screen; Behind it's first fold reads "What it was meant to do · Done when: 4 met · 2 your check"; a sheet with a Not yet line shows it at the top of What changed; a card with no review looks as today.

## Decisions
- **D1. With a stored review sheet, no "What it's about" plate at the top.** What changed (or, without one, the next part the sheet has) comes straight under the head, after "Needs your answer" when there is one. Without a sheet the plate stays as it is: before the review it is the only place saying what the card will do.
- **D2. Not yet lines head What changed.** Each bullet of `done_check` starting `**Not yet:**` is drawn at the top of What changed's body, in one `.not-yet` block with the label "Not yet · from Done when" and `.card-plate.asks`'s hazard edge, only when there is one. A sheet with Not yet lines but no `changed` shows them in a "What changed" plate of their own.
- **D3. "What it was meant to do" is Behind it's first fold**, closed, holding what the plate holds today (What it will do, then Done when as of now or the plan's Done when). Its gist is the tally from `done_check`; without `done_check`, no gist. "Your note and how it grew" keeps the note, as today.
- **D4. One tally, two pages.** The function that counts `done_check`'s bullets by their first label and returns the tally and the Not yet lines lives in `factory_dashboard/milestones.py`; `thread.py` (which already imports from it) uses it from there. If f261-02 built it in `thread.py`, the ticket moves it. Builds on: F216's `done_check`, F261's tally, the existing `gists` and `.folds`. Makes removable: the `show_note` juggling in `milestone.html` that hid the note only on a reviewed page (the note now always lives in "Your note and how it grew" once there is a sheet), removed in the same ticket.
- **D5. The owner's rule changes with it.** "Expected against actual, first" in `runner/instructions/author/owner.md` becomes: on a reviewed milestone, what changed comes first, and a Done when line not yet met heads it; the expected outcome and the rest of Done when fold behind it. Before the review, the expected outcome and Done when stay first.
- **D6. Who builds:** 01 developer (a template, `milestones.py`, CSS, after f261-02, which writes the tally and touches the same thread code). 02 lead (protected `runner/`), one line, no wait on 01.

## Before and after
- `/milestones/f286-i-want-code-reviews-to-highlight`
- `/milestones/f261-the-review-notes-on-the-planning`

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | review-opens-on-what-changed | developer | 3 | f261-02 | D1–D4 |
| 02 | owner-rule-what-changed-first | lead | 1 | – | D5 |
