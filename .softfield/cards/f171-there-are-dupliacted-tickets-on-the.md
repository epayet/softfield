# Milestone F171: Each card once on the board, and fix tickets named after what they fix

> **State:** done · **Priority:** 7 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-05. Base: git tag `f171-there-are-dupliacted-tickets-on-the-start`. Report: [`.softfield/reviews/f171-there-are-dupliacted-tickets-on-the.md`](../reviews/f171-there-are-dupliacted-tickets-on-the.md).
> Planted by the owner on 2026-10-22.

## Notes
there are dupliacted tickets on the travel companion board. also the ticket name picking looks fishy and buggy

## Plan (lead, 2026-10-22)
- **Why the board doubles cards:** travel-companion's F4 tickets and its F2 ticket say `milestone: f4` / `milestone: f2`, the short form. `runner/instructions/task-format.md` lets frontmatter take either form, but `record_ticket` (`runner/loop.py`) files the ticket under the key as written, so the database grew a second, empty milestone row `f4` (and `f2`) beside the card's row `f4-after-my-message-i-have-the`. The board makes a card of every row, and `_placed` (`factory_dashboard/board.py`) keys its cards by `F4`, so both show as the last one read: twice, "F2" with no title, and the real F2 lost its ticket. Softfield's own board has the same fault in another shape: a planner job on a card merged away (F107, F29, F44) leaves an empty row by its short key, and "F107" shows in Planted with no title.
- **Why fix tickets have odd names:** a stand-in checkpoint's fix ticket is named from the first four words of the finding's sentence (`fix_ticket`, `runner/loop.py`), so it stops mid-phrase: `f1-14-fix-the-been-test-does`, `f114-09-fix-notification-tests-do-not`.
- **Why travel-companion went from M1 to F1 (owner, 2026-10-22: "confused if it should pick m or f"):** a card's letter is its area's (`SERIES` in `runner/planner.py`: factory `f`, product `m`), and a note from the Plant box carries no area, so `_area` makes it factory: every card planted since M1 is an `f`, product work too, and the lead set some to product afterwards, leaving the letter behind.
- Tickets: `f171-01-tickets-join-their-card` (lead, runner), `f171-02-board-shows-cards-only` (developer, dashboard), `f171-03-fix-tickets-named-by-their-ticket` (lead, runner), `f171-04-plant-takes-the-projects-area` (lead, runner). None waits for another.
- No mock-up: the board goes back to the look it meant (each card once, with its title); the names are wording.

## Decisions
- **D1: the runner reads a ticket's milestone as its card's full key,** in one place, wherever it reads a ticket (`full_key` in `runner/tasks.py`, as `backfill` already does): its row, its jobs and its findings go under the card's row. A short key whose card has no doc stays as written. Pre-flight keeps taking either form (`runner/instructions/task-format.md`).
- **D2: an empty short-key row is folded into its card's row** when the project has one whose short key matches and that is not removed: its tickets, jobs and findings move, then the empty row goes. Only a row with no title, state, status or sign-off of its own is folded; anything else is left as it is.
- **D3: the board and the milestones list show a milestone row only when it is a card** (it has a state) **or has tickets.** A row with neither (F107's) is no card.
- **D4: a fix ticket is named by the ticket at fault:** `<prefix>-<nn>-fix-<its slug>`, the slug being the ticket at fault's id after `<short key>-<nn>-`, with a leading `fix-` dropped and at most four words, plus `-tests` on a `tests_only` one. `f1-11-fix-restamp-been-and-undo`'s weak test becomes `f1-14-fix-restamp-been-and-undo-tests`. Ids of tickets already written stay.
- **D5: a note planted with no area takes its project's,** `area` under `[project]` in `.softfield/project.toml` (factory or product); missing, it is product. Softfield's says factory. Its key follows, as now. Keys already given stay: a key is in its card's file name, its thread, its plan branch and its tickets' ids, so renaming costs more than the letter is worth.
