# ADR 27: The lead does small things when asked, and says what it did

- **Status:** Proposed
- **Date:** 2026-10-08
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 20](20-planning-room.md) item 6 ("the lead only proposes"), for the actions listed in item 1 below. F49 D1 already makes merges apply at once; this ADR widens that to a short list.
- **Evidence:** F58, the owner's plant (2026-10-08): "can it do things, like if i ask to replan for me. or just plan? or do something and let me know what it did?". F57, the same day: "reprioritise for me while i dont have access to an editable board". Today a planner job can only write drafts on `plan/<card>` (`DRAFTS` and `is_draft` in `runner/planner.py`); to move a card up the owner has to use the dashboard's arrows, which F54 says do nothing.

## Context
- The owner treats a thread as a conversation with someone who can act. Asking "put F31 first" today gets a reply that suggests it, then the owner has to do it by hand.
- What the lead does on main through a request already exists, with its commit and its undo: `priority` (f6-18), `drop_seed` (f6-17), `archive`, and the merge steps F49 applies at once. Each one moves bookkeeping only: no ticket is queued, no code changes, and each is undone in one move.
- Plans, replans and ADRs choose what the factory builds and what Claude spends. The one-tap approval is where the owner sees that before it happens; it stays.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ The lead acts at once, on request only** (amends ADR 20 item 6). When the owner's message asks for one of these, in so many words, the lead does it in the same job:
   - **priority:** set a card's or a waiting ticket's priority (any card, from any thread);
   - **drop:** drop an idea card that is done or no longer needed (f6-17, F25 D3);
   - **archive:** archive or unarchive a thread.

   Merges keep F49's rule (at once, at the lead's own initiative). Nothing else is done at once.
2. **How:** the lead's JSON block gets an `actions` list, beside `points` and `proposals`: `{"kind": "priority", "subject": "f31", "value": 0}`. After the job, the runner applies each through the existing request steps (`_priority`, `_drop_seed`, `_archive` in `runner/requests.py`), in one commit on main, "… by the lead" instead of "… by the owner". An action the runner refuses (no such card, a ticket in progress) is listed as refused, with why.
3. **The owner sees what was done:** the reply shows a "Done" line per action, at the top ("F31: priority 100 → 0"), and a refused one in orange with its reason. The thread's reply says the action in words too.
4. **Undo by asking,** as F49 D6: "put it back" on the same thread is another action. No Undo button.
5. **What stays a proposal:** plans, replans (they change waiting tickets the line will build), ADRs, mock-ups, seeds. "Replan F10 for me" gets a replan drafted in the same reply, one tap from the desk, as today. A replan is still only for the card's own thread (f6-13), so the lead says so when asked from another thread, and moves the conversation there.

## Consequences
- The owner can reprioritise, drop and tidy from a phone by asking, without an editable board (F57 until F5's board).
- The lead now writes to main without a tap, for bookkeeping. The cost of a misread request is one wrong priority, seen at once on the thread and undone by asking.
- The prompt grows by a short paragraph on `actions` and when they apply.
