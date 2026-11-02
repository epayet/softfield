# Review: F90, a card's page shows your whole note

- **Status:** done, signed off by the owner on 2026-10-23.

## Sign-off sheet

### 1. What changed
A card's page in the Planning room now shows what you planted, word for word, under its title. Before, a plain plant showed only its title, cut under 60 characters ("is the planning conversation efficient atm, in terms of…"), and the rest of your note was only in the card's file.
- **A seed you haven't sent yet:** the whole note sits in a panel right under the title, above the reply box.
- **A card with a conversation:** the note is folded under **Your note**, so a long thread isn't pushed down; tap it to open.
- **A merged card:** the notes it gathered show as plain lines ("From F18: Arrow to reprioririse queue (merged by the owner on 2026-10-13)"), without the file's `###` marks.
- A card with no note shows nothing extra. The note is read-only: anything you want to add goes in the reply box, which the lead reads with the card (D1).

### 2. How to test it yourself
1. On the phone, open Planning, then F83 ("is the planning conversation efficient atm, in terms of…"). Under the title, the panel reads the whole note: "is the planning conversation efficient atm, in terms of claude token usage?".
2. Open F15 (Reprioritising tickets), which has a conversation. Under the header, tap **Your note**: your note opens, then "From F18: Arrow to reprioririse queue (merged by the owner on 2026-10-13)" and F18's note, with no `###`.
3. Plant a new idea of two or three long sentences, without "ask the lead". Once it shows in Planted, open it: the whole text is under the title.

### 3. Left for later
- Two runner tests that depend on timing fail now and then (backlog, with the fix). They cost this card an extra Opus run ($0.32) though the work was right.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-09: planned by the lead in one planner job ($0.88); then the card waited its turn on the board.
- 2026-10-23 12:52 ([session](../sessions/2026-10-23-1252.md)): `f90-01-seed-shows-its-note`, a lead ticket. Sonnet built it in 5 minutes ($0.28); the runner's checks then failed on an unrelated timing test, so Opus stepped up (8 minutes, $0.32), found the work right and passed on a rerun.
- Lessons:
  - A flaky test makes ADR 32's Sonnet trial look worse than it is: this step-up was the gate's failure, not Sonnet's. Read the step-up's log before counting it.
  - The note is stored as Markdown the factory writes (merge headings, escapes); a page that shows it has to undo the factory's own marks. Fixed in the review.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** fix the two flaky timing tests soon (a small lead ticket), since every failure of them pays for an Opus step-up or a developer retry. Later, if you find yourself wanting to correct a planted note rather than add to it, a small "edit the note" request is possible; D1 left it out on purpose, and I'd wait to see whether the reply box is enough.

### 7. What clogged the factory line
- **Planned to built, 14 days** (planner job 2026-10-09 21:45, first ticket 2026-10-23 13:30): the card waited its place on the board behind the cards above it. Nothing to unclog: the board's order working.
- **The ticket waited 26 minutes in the run** (12:52 to 13:30) behind `f142-04` and its checkpoint, by order.
- **8 minutes and $0.32 on an Opus step-up** that changed nothing: a flaky `tests/runner/test_loop.py` test failed Sonnet's checks. Unclog: the backlog fix for the two timing tests.

## What was built
- `factory_dashboard/planning.py`: `_note(repo, thread)` reads the card's doc in the project's checkout (`milestone_file(repo, "cards", full_key(…))`) and returns the text between `## Notes` and the next `## ` heading, stripped; "" with no checkout, no doc, no section, "(none)" or the general thread. `thread_page` passes it to the template.
- `factory_dashboard/templates/thread.html`: `#note` under the header, a plain panel with no thread, a folded `<details>` "Your note" with one; `white-space: pre-line`, escaped by Jinja (no `| safe`), 44 px summary like the page's other summaries, themed from the page's tokens.
- Four tests in `tests/factory_dashboard/test_planning.py`: a 120-character note shows whole and escaped, and stops at the next section; the folded version with a thread; no note for no section, "(none)" and the general thread; no note for a repo that isn't a folder here. No existing test was edited.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The note showed the factory's own marks raw: F15's live page read "### From F18: …", and a quoted line would show its escaping backslash | Fixed: `_note` drops a heading's `#`s and the backslash `seed_card`/`merged_card` put before `>` or `#`; test `test_a_merged_note_shows_without_the_factorys_marks` |
| F2 | should-fix | backlog | Two timing tests in `tests/runner/test_loop.py` fail now and then; one failed Sonnet's right work here | Backlog, with the fix (a tolerance on the fake clock, a deadline for the beats) |

Checkpoint verdicts: no checkpoint ran (one lead ticket).

Score: 8/10. Small, careful and on the plan: read-only, escaped, no new route, tests covering every Done-when case. F1 was the one thing the plan didn't foresee, and the real F15 page showed it.

Checked and fine: the thread name can't reach outside `.softfield/cards/` (a path segment has no `/`, and `full_key` only maps to existing docs); a missing or unreadable doc renders the page without a note; a `### ` subheading inside Notes doesn't end the section; the note comes after `#card` on the page. Live pages read with `softfield look page`: F83 shows its whole note, F15 its folded one. With the review's fix, ruff, the format check and mypy pass on the changed files; `tests/factory_dashboard/test_planning.py` passes in full (222 tests); `tests/runner` and `tests/factory_dashboard` together ran past 90% with no failure before the run was stopped at its time limit (the errors printed after the stop are tests cut off by it) (a known limit, ticketed among bug-05 to bug-07).

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
- Added: [f90-review should-fix, F2] the two flaky timing tests in `tests/runner/test_loop.py`, with their fix.

## Factory
- Flow: one lead ticket, two attempts (Sonnet, then Opus's step-up after a flaky gate); no checkpoint, no stops, no limit waits, no interventions by you after the plan.
- Models: Opus planned ($0.88) and stepped up ($0.32); Sonnet built it ($0.28). No local tokens: the ticket was the lead's.
- What worked: Sonnet on an easy lead ticket (difficulty 3) built it right the first time, as ADR 32 hoped.
- What didn't: a flaky test turned a pass into a $0.32 step-up, and would count against Sonnet in ADR 32's trial if read from jobs alone. What to change: fix the tests (backlog), and read a step-up's log before scoring it (ADR 02's log). The ticket also named `.softfield/milestones/`, the cards' old folder; the lead used `cards/`. Ticket craft: name paths from the code, not from memory.

<!-- runner report -->
<!-- /runner report -->
