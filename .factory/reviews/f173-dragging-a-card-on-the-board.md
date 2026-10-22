# Review: F173, the board's order is the order the work runs in

## Sign-off sheet

### 1. What changed
Dragging a card on the board now decides when its tickets run, and nothing else does. Before, a ticket with its own `priority:` number ignored its card's place: F153's tickets said 100 and would have run last even with the card dragged to the top. Now a feature ticket has no number of its own: it runs in its card's place, and inside a card the tickets go by what they wait for, then by their number. Bugs keep a number, but it is only their place on the board, written when you drag them. Next in line, the line and a card's page show the same order the runner picks.

### 2. How to test it yourself
1. On the board, drag a card with ready tickets (for example F171) to the top, and send.
2. On the overview's Next in line, after the runner's next pick: that card's tickets come first, each showing the card's priority (0), whatever they said before.
3. Drag a bug between two cards and send: it shows in Next in line between their tickets.
4. Open the card's page: its ready tickets are listed in the same order as Next in line.

### 3. Left for later
Nothing. The ↑ ↓ arrows you planned to remove are already gone from Next in line; a request to move one feature ticket on its own is now refused with "a ticket runs in its card's place: move the card on the board".

### 4. Decisions waiting for you
None. The plan follows your own words on the card ("it should just follow the board order"), already recorded in `docs/agents/owner.md`.

### 5. How the work went
- 2026-10-22 21:39 ([session](../sessions/2026-10-22-2139.md)): 1 ticket, `f173-01-board-order-only`, built by the lead (runner code), merged first time in 14 minutes for $2.52; 0 local tokens. The runner then stopped, as designed, because `runner/` changed.
- Lessons: the ticket changed six existing tests honestly (their old expectations were exactly the behaviour being removed), but one edit weakened its check to the first two rows, and the new rule for fix tickets had no test. The review added both.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** with the board as the only order, the next useful step is F15's "drag, then one send" for bugs and cards together on one board, which this makes simple: there is one number per card and per bug, nothing hidden underneath. ADR 27 (the lead acts when asked) still says the lead may set "a waiting ticket's priority"; from now on that only works for bugs, which the refusal message explains, so no change is needed unless the planning room starts offering it.

### 7. What clogged the factory line
- Nothing in this milestone: one 14-minute lead job, no limit waits, no failed attempts, no stops for you. The run ended on the designed stop for a `runner/` change; a fresh process is the only cost.

## What was built
- `runner/tasks.py`: `task_priority` reads a bug's own `priority:` (50 when none) and a feature ticket's card's place (100 when none), never a feature ticket's own number (D1). Pre-flight refuses a `priority:` on a feature ticket (`FEATURE_PRIORITY`, D2).
- `runner/requests.py`: the `priority` request refuses a feature ticket with `CARD_PLACE` (D3); the reorder's docstring follows.
- `runner/loop.py`: `fix_ticket` copies a source's priority only onto a bug's fix.
- `factory_dashboard/queries.py`: `ticket_priority` and `in_run_order`/`run_order` take the card map as the runner does (D5).
- Five ready tickets lost their `priority:` (f103-01, f171-03, f171-04, f21-03, f5-13); no feature ticket in ready/ or later/ carries one now. `docs/task-format.md` and `docs/agents/lead.md` say the same (D4).

Tests: new cases in `tests/runner/test_tasks.py` (card beats a ticket's number, inside a card by `depends_on` then id, pre-flight), `tests/factory_dashboard/test_queries.py` (run order across two cards and bugs) and `tests/runner/test_requests.py` (refusal). Edited existing tests, each checked: the priority-request tests moved from feature tickets to bugs; the reorder test, the card page's order and Next in line now expect the card to win; `conftest.write_later_priority` moved its "own priority" ticket to bugs. Each edit matches D1 to D5; none hides a regression.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | `fix_ticket`'s new rule (no priority on a feature ticket's fix) had no test, while done feature tickets still carry old numbers | Fixed: `test_a_fix_ticket_on_a_feature_ticket_drops_its_old_priority` (`tests/runner/test_loop.py`), fails without the change |
| F2 | nit | claude | The edited Next in line test checked only the first two of three rows | Fixed: it asserts the whole order |

No checkpoint ran (the only ticket was a lead ticket), so there are no checkpoint verdicts. Score: 8/10: a clean change that matches every decision, with good new tests; one changed rule was untested and one edited test was looser than before.

Checked and fine: every reader of a ticket's priority (`work_stands`, the dry run's dispatch, `/tickets`, set-aside list, the reorder's board) goes through `task_priority` or `ticket_priority`; ruff, mypy and the 2504 runner and dashboard tests pass.

The French: no `coucou/locale/fr/` change in this milestone.

## Factory
- Flow: one lead ticket, first attempt, no stops for the owner, no limit waits, no parks; the designed stop for a `runner/` change ended the run.
- Models: Claude Opus built it ($2.52); the local model had nothing to do (protected runner code).
- What to change: when a ticket changes who gets a field (here, which tickets keep `priority:`), every writer of that field needs a test, not only its readers. `fix_ticket` was the one writer missed. Once is not a pattern yet; worth a line in `docs/task-writing.md` if it recurs.

<!-- runner report -->
<!-- /runner report -->
