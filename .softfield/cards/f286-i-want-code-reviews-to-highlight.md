# Milestone F286: Reviews look for complexity and leave the code simpler (Boy Scout rule)

> **State:** ready · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-21.

## Notes
I want code reviews to highlight refactoring and reduce complexity opportunities when it finds them. The cards suggested to plant at the review page kind of do this already. I want to make sure that we're making the product and the factory less complex over time, not more. Boys scout rule

## What we know (2026-11-23)
- `prompts.REVIEW` (`runner/prompts.py`) asks for bugs, weak tests, the French and the mock-up; nothing asks for complexity. Of the 23 quoted "What next" lines in `.softfield/reviews/`, one is a simplification (F264's dead wait machinery).
- `runner/loop.py` is 6,565 lines; since 2026-10-23 it gained 1,411 lines and lost 497 over 41 commits.
- A review's numbers (`softfield report`, `runner/report.py`) count tickets, attempts and dollars, never whether the code grew. `tickets."commit"` holds each merged ticket's squash commit.

## Outcome
Every review looks for complexity and says it: the milestone's own as a fix, older complexity in the files it touched as at most two "Simpler:" lines to plant, and its numbers show the code lines it added and removed, beside every earlier milestone's.

## Done when
- the next milestone reviewed after this card has a "Code lines" row and a "Net code lines" trend in its numbers
- a review that finds a duplicate or dead code the milestone added grades it should-fix and routes it
- a review that finds older complexity in a touched file writes it as a quoted line starting "Simpler:", at most two
- a plan that adds a mechanism names what it builds on and what it makes removable
- Softfield's next review has no "Product: on hold" line; its "What next" carries feature ideas for Softfield under Factory
- no review brief mentions French

## Decisions
- **D1. The rule is ADR 52** (`.softfield/adr/52-a-review-leaves-the-code-simpler.md`): items 1–3 for the review, 5 for the planner.
- **D2. "Simpler:" is a word, not a new kind of line.** It is the first word of an ordinary quoted line under Product or Factory, so `review_ideas` (`factory_dashboard/milestones.py`) and the Plant buttons need no change. No mock-up: nothing on screen changes.
- **D3. Checkpoints don't change**: bugs only (ADR 52, "What doesn't change").
- **D5. What next, by project** (ADR 52 items 6–8, owner 2026-11-24): at most two feature ideas that follow from the milestone. On Softfield there is no Product bullet: Softfield is the product, so everything goes under Factory and plants on Softfield's board. Other projects keep Product (the project) and Factory (Softfield). "Check the French" leaves `prompts.REVIEW` and `docs/workflow.md`; F280 (The factory's instructions name no project) removes it from `lead.md` and keeps Coucou's line, so 01 waits for f280-01.
- **D4. Code lines** are computed from git each time (`--numstat` of each merged ticket's commit), leaving out `tests/`, `docs/`, `.softfield/` and `*.md`; nothing stored, no gate.

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | review-looks-for-simpler | lead | 3 | f280-01 | D1, D2, D3, D5 |
| 02 | code-lines-in-review-numbers | lead | 4 | – | D4 |
