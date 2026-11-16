# Milestone F249: A sent-back plan shows on its way on the desk and its thread

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-14.

## Notes
A plan is being sent back but the answers wanted box is not orange dotted

## Plan (lead, 2026-11-16)
- **Why the box stays solid:** the desk dashes a card's box when the lead owes it a reply (`_waiting_order` in `factory_dashboard/planning.py`). That counts an open `plan_message` request (`_asked`), or the owner's stored message with a planner job open, but never an open `send_back` request. Between the press and the runner's next pick, the card's last message is still the lead's, so the box reads "the lead replied … ago", solid and counted. On top of that, `_listed` keeps only open or on-its-way proposals, so the sent-back plan's link drops out of the box. Seen on 2026-11-14: F133's plan was sent back at 10:17 and picked up at 10:19.
- **The thread page has the same gap:** `factory_dashboard/thread.py` shows an open `plan_message` as the owner's waiting message and says the lead is writing, but not an open `send_back`, so the comments the owner just sent show nowhere until the pick.
- No mock-up: the dashed orange "on its way" box and the waiting message already exist; this makes a sent-back plan use them.
- Ticket: `f249-01-sent-back-shows-on-its-way` (developer).

## Decisions
- **D1: an open `send_back` counts as a message waiting for the lead,** for the card before the `/` of its subject, wherever an open `plan_message` does on the desk (`_asked`). The box is dashed, says "being revised" and when the reply comes, and leaves the count, as for a message.
- **D2: a sent-back proposal stays in its box, dashed,** until the lead's next reply replaces the set: `_listed` keeps a `sent back` proposal as on its way.
- **D3: the thread page shows an open `send_back` as the owner's waiting message,** its comments as numbered points, as it shows an open `plan_message`.
