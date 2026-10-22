# Milestone F173: The board's order is the order the work runs in

> **State:** ready · **Priority:** 0 · **Area:** factory
> Planted by the owner on 2026-10-22.

## Notes
Dragging a card on the board doesn't move its tickets when they carry their own priority: F153's said 100 and ran last whatever I did. A drag should win over the tickets' own numbers. I want to be able to prioritise work clearly.

## Plan (lead, 2026-10-22)
- **Why it happens:** `task_priority` (`runner/tasks.py`) takes a ticket's own `priority:` before its card's, so a ticket a planner numbered runs by that number, whatever the card's place. On 2026-10-22 F153's two tickets said 100 and F172's three said 2: with the cards dragged to the top, F153 would still have run last. The lead removed those five numbers by hand (2011136). ADR 19 item 3 gives a priority to a card and to a bug ticket only; a feature ticket's own number winning across cards came later (f6-18's ↑ ↓ on Next in line).
- **The fix (owner, 2026-10-22: "i doubt the need of the priority field at all, it should just follow the board order"):** the work runs in the board's order and nothing else. A feature ticket has no `priority:`: inside its card, tickets run by what they wait for, then their number. A bug, which has no card of its own, keeps a `priority:`, but only as where the board has placed it, written by a drag.
- Ticket: `f173-01-board-order-only` (lead: the pick order is read in the runner, mirrored on three dashboard pages, and checked at pre-flight).
- No mock-up: nothing on screen changes but the order the line shows.

## Decisions
- **D1: the pick order is the board's.** `run_order` (`runner/tasks.py`) sorts a feature ticket by its card's priority (its place on the board; 100 when the card gives none), then milestone order, then id; a bug ticket by its `priority:` (50 when none). `Task.priority` is read for bugs only.
- **D2: a feature ticket's `priority:` goes.** Pre-flight (`check-tickets`, Approve) refuses it on a feature ticket, saying the board orders the work; the lead strips it from the tickets in ready/ and later/ in the same change (f151-01, f171-03, f171-04, f103-01, f5-13, f21-03 have one today). `docs/task-format.md` says `priority:` is a bug's place on the board, written by the board.
- **D3: the `priority` request takes bugs only.** Its ↑ ↓ on a feature ticket (f6-18), which the owner plans to remove, is refused with "a ticket runs in its card's place: move the card on the board".
- **D4: a ticket that repairs main** goes first by `depends_on` alone: every ready ticket waits for it, so nothing else can be picked. `docs/agents/lead.md` drops its `priority: 0`.
- **D5: the dashboard reads it the same way:** `ticket_priority` and `in_run_order` (`factory_dashboard/queries.py`) follow `run_order`, so Next in line, the line and a card's page show the order the runner picks.
