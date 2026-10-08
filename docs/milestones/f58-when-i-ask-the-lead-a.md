# Milestone F58: when i ask the lead a question through planting an idea

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
can it do things, like if i ask to replan for me. or just plan? or do something and let me know what it did?

### From F57: reprioritise for me while i dont have access to an editable board (merged by the owner on 2026-10-08)
planner able to answer my questions and plans smoothly > view on current priorities and reprioritisation (editable board)

## What happens today (read in the code, 2026-10-08)
- **Plan:** yes. The lead drafts the card's doc, tickets, ADRs and mock-ups on `plan/<card>`; Approve plan queues them.
- **Replan:** yes, as a draft: on a building card's own thread, it may edit, add or set aside that card's waiting tickets; one tap applies it (f6-13). Not from another card's thread.
- **Do it and tell me:** no. ADR 20 item 6, "the lead only proposes". The one exception coming is F49: merges apply at once.

## Expected outcome
Asked on any thread to reprioritise a card, drop a done idea or archive a thread, the lead does it in the same reply and says so at the top ("Done: F31 priority 100 → 0"). Plans, replans and ADRs stay one tap away. See [ADR 27](../adr/27-the-lead-acts-when-asked.md) (Proposed).

## Tickets
Written once ADR 27 is accepted. Likely one lead ticket, after f49-01 (same "apply after the planner job" step): `actions` in the reply's block, applied through `_priority`, `_drop_seed` and `_archive`, a "Done" line on the reply.
