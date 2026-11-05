# Milestone F216: A shorter, consistent review page, with the decisions made along the way

> **State:** ready · **Priority:** 9 · **Area:** factory
> Planted by the owner on 2026-11-04.

## Notes
Let's redesign the milestone review page it's very inconsistent and long to read. The decisions from you is always either empty or not very interesting (just says what adr was involved). I prefer a 'decisions I made along the way' or similar especially if it's decisions it took that were not thought of during planning that the model thought was a good idea. Separately, I wonder if the reviews are currently expensive to run to write this kind of reports? Let's make sure it's useful if it's rich

## What we know (2026-11-04)
- **Decisions waiting for you says little.** 79 of the 88 stored sheets start "None", and 13 mention an ADR that was already accepted or a point already settled. Choices made along the way do get written, but below the sheet, in parts of the report no page shows: F187's "What was built" and findings hold its changes outside the plan, and F175's lessons hold its unplanned fix.
- **The page is long and uneven.** `factory_dashboard/templates/milestone.html` draws 15 parts one after another. "What it's about" and "Before and after" are themed plates, the rest are bare sections. Findings shows twice, as counts. Sign off sits above the review it signs off. Empty parts say "Not written yet" or "No runs."
- **`_to_html` causes the rest of the unevenness** (`factory_dashboard/milestones.py`): it knows `- ` bullets, and `**` only inside them. Numbered steps come out as paragraphs, nested bullets go flat, and backticks and `[session](../sessions/…)` links show as raw text.
- **What a review costs.** $1.82 a job on Opus: $216.54 of $1,353 on Claude so far (16%), and $134 of $705 since 20 October (19%). Planner jobs are the largest share, at $575 (43%). The last 15 cards averaged $3.04 of review each, 31% of what those cards cost.
- **Writing the report is the small part of that.** F187's review wrote 48,296 tokens in 127 turns, and its whole report is about 3,500 of them (an estimate from its length). Nine of its 100-odd tool calls were `softfield look sql`, there for the report's hours. So the report costs about a tenth of a review at most. The rest goes on reading the diff and fixing what it finds.
- **What the money buys.** Reviews fixed 173 blocking or should-fix findings themselves, among them F187's two bugs that would have started on 28 March.

| Card size | Cards | Review, average | Share of card | Blocking or should-fix per card | Reviews finding none |
|---|---|---|---|---|---|
| 1–2 tickets | 46 | $1.67 | 30% | 1.4 | 8 |
| 3–5 tickets | 22 | $2.75 | 28% | 3.7 | 1 |
| 6+ tickets | 22 | $3.76 | 13% | 8.2 | 2 |

## Outcome
A card's page reads as one thing: what it was meant to do and whether it does, what changed, how to test it, the choices made along the way that the plan didn't make, then Sign off. Everything else folds away with a line saying what's inside. Reviews stop writing what no page shows or what the runner already knows.

## Done when
- the next review's page shows "Decisions made along the way" with what was chosen, why and who chose it, or no such plate when there were none
- "Needs your answer" shows straight under the head only when a decision waits for the owner; "None." no longer shows on any page, old reviews' included
- Sign off comes after the review's reading part, and What next after it
- the parts after What next are folds in one plate, each with its one-line gist; an empty part doesn't show
- "What the review caught" lists the card's findings with what happened to each, and "What it cost" says the review's dollars beside the card's total
- numbered steps, nested bullets, backticks and links render properly on old reviews and new
- a review's report is its sheet and the runner's numbers, with nothing below the sheet

## Decisions
- **D1. The sheet's new shape,** in `runner/instructions/lead.md`, "Sign-off sheet", and `REVIEW` in `runner/prompts.py`. Its headings, in order: `### 1. What changed` (at most 4 points of 2 lines), `### 2. How to test it yourself` (at most 5 steps), `### 3. Done when, as of now`, `### 4. Decisions waiting for you`, `### 5. Decisions made along the way`, `### 6. What next`, `### 7. Left for later`, `### 8. How the work went`, `### 9. What clogged the factory line`. A section with nothing to say is left out, heading and all, except 1 and 2. These caps are the prompt's words, with no gate.
- **D2. Decisions made along the way.** At most 5 bullets. Each is a choice the plan didn't make or changed: an addition, a departure from a card's D or a ticket, or something left out on purpose. Each says what was chosen, why, the other option if there was a real one, and who chose it (the review, or the lead or developer on a named ticket), in the form `- **What was chosen.** Why. *Who.*`. It is not a plan's decision built as written, an ADR, or a plain bug fix that changes no behaviour. The source is the review comparing the card's Decisions, Done when and mock-up with the diff and its own fixes. No new step for workers: if three reviews come out thin, tickets can report their choices too.
- **D3. Done when, as of now.** One bullet per line or group of the card's Done when, starting `**Met:**`, `**Not yet:**` or `**Your check:**`. The page shows it in place of the plan's Done when, and falls back to the plan's list on a sheet without it.
- **D4. Decisions waiting for you** holds only what needs the owner's answer: a draft ADR or a question, with the recommendation. On the page it becomes "Needs your answer", straight under the head. A stored sheet whose text starts "none" (any case) shows no plate: old reviews need no rewrite, and the full text stays in the report file.
- **D5. How the work went** keeps at most 3 lessons, one or two lines each, and no line per session: the Tickets and Runs folds have those. **What clogged the factory line** keeps only hours with a fix, at most 3 lines, and is left out otherwise.
- **D6. Nothing below the sheet.** A report is the title, the status, the sheet and the runner's numbers block. "What was built", the findings table, "What was set aside" and "Workflow observations" stop: findings live in `findings`, and a workflow lesson goes under How the work went. `docs/workflow.md`'s "Report" paragraph says the same. Old reports stay as they are.
- **D7. New sheet keys.** `SIGNOFF_SECTIONS` in `runner/milestone.py` gains `"Done when, as of now": "done_check"` and `"Decisions made along the way": "along_the_way"`. No schema change: the sheet is stored as JSON in `milestones.signoff`. Old sheets simply lack the keys.
- **D8. The page, once a sheet is stored** (the picture is `.softfield/cards/f216-mockup/review-page.html`). Head; Needs your answer; What it's about (outcome and Done when, as of now); What changed; Before and after; How to test; Decisions made along the way; Sign off; What next; then one plate, "Behind it", of closed `<details>`, each with its gist: Left for later, What the review caught, Lessons, What clogged the line, What it cost, Your note and how it grew, Tickets, Runs. Every plate uses one class, the `.about` plate's rules under a shared name, and the inline styles go. A card with no sheet keeps today's page. No new colour token; no script.
- **D9. The gists are the page's own,** counted or derived, never written by the review: item counts, "7: 5 fixed, 2 left as they are", "$7.61, of which the review $2.85", "3 of 3 done". A section whose stored text isn't in bullets shows only its name, with no gist.
- **D10. What it cost** replaces Results, Savings and Findings' counts: a to-scale row per job role from `jobs.cost_usd`, in plain words, in the rules' ink, no agent or status colour; then the review's score and rounds, and "Developers, first time: n of m". Savings show only when `savings.lines` is above 0. A role with no dollars and no jobs doesn't show.
- **D11. What the review caught** reads `findings` for the card, in order of severity then key: severity, summary, and "fixed" (resolved), "left" (route `report`), "ticket" (route `local` or `later`) or "for you" (route `adr`). The old route `backlog` reads "ticket". It's read straight from the database, so it works on every old card.
- **D12. `_to_html` learns** `1.` lists, one level of nested bullets, `**` everywhere, `` `code` ``, and `[text](url)`: a link for `http(s)` only, the text alone for anything else, since a relative path leads nowhere on the dashboard. It escapes first, as it does now. It keeps F164's quoted lines as F164 left them.
- **D13. The thread.** `_SHEET` in `factory_dashboard/thread.py` becomes What changed, How to test, Decisions waiting for you, Decisions made along the way; a `decisions` starting "none" is left out, as in D4. Its Sign off stays where it is.
- **D14. Order and who builds.** All three wait for F164, Plant a review's ideas, since they touch the same prompt lines, `_to_html` and template. 01 lead (protected). 02 developer (a query and a parser, `queries._findings` and the existing `_to_html` tests are the examples). 03 lead: template work on these pages cost developers hours in F19 and F28, as F164's D6 found.

## Before and after
- `/milestones/f216-let-s-redesign-the-milestone-review`
- `/milestones/f187-store-every-time-in-utc-the`
- `/planning/f216`

## Later
- F200, Where the hours went: gives `softfield report` the hours, so reviews stop writing their own queries for What clogged the line. Its own card.
- Workers reporting their own choices, if D2's reviews come out thin.

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | review-sheet-new-shape | lead | 3 | f164-01 | D1, D2, D3, D5, D6, D7 |
| 02 | findings-costs-and-markdown | developer | 4 | f164-03 | D10, D11, D12 |
| 03 | review-page-plates-and-folds | lead | 5 | 01, 02, f164-03 | D3, D4, D8, D9, D10, D11, D13 |
