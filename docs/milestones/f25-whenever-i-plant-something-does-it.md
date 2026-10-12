# Milestone F25: whenever i plant something, does it check the current state of things in case the seed is not relevant anymore?

> **State:** ready · **Priority:** 3 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Notes
- The owner's question (2026-10-07): when they plant, does the lead check the current state, in case the seed is no longer relevant?
- What happens today (read in the code, 2026-10-07):
  - "Plant and ask the lead" writes the card and queues the lead's reply on its thread at once (`_plant` in `runner/requests.py`), on Opus. "Plant" alone writes the card only; the lead answers when the owner first writes on its thread.
  - The lead's prompt (`_PLANNER_HEAD` in `runner/prompts.py`) asks for one check only: does the seed repeat a card in state idea, planning or ready, or another thread? It never names work that is done or being built, nor the code's history.
  - `docs/agents/owner.md` asks to "answer from the code and the queue", so the lead usually reads the code, but nothing in the prompt makes it ask "is this already done, or no longer true?".
  - After approval, nothing checks again. Pre-flight only checks that the ticket's paths and names exist. A ticket that went stale gets "the attempt changed no file" three times, then an escalation, where the lead finds out.

## Expected outcome
When the owner plants a seed, the lead's first reply says whether it is still needed: already done (and by what), made moot by later work, or open. A seed that isn't needed comes with the suggestion to drop it (the Drop button, f6-17), or to merge it if a building or done card covers it.

**Done when:** the planner's prompt asks for that check against the code, `git log` and the cards being built or done, and a test holds it.

## How to test it
Plant a seed for something already fixed (for example "the pause button does nothing the first time" once F28 is done). The lead's reply should start with a point saying it is already done, name the commit or card, and suggest dropping the seed.

## Decisions
- **D1. The check runs in every reply the lead writes on the thread, all before approval.** "Plant and ask the lead": in the first reply, straight after planting. "Plant" alone: in the first reply to the owner's first message on the thread. Each later reply (a comment, a send-back) checks again, since every reply gets the same instructions. Once the plan is approved, nothing checks again when a ticket is picked: that would cost a Claude call per ticket to catch a rare case that the "changed no file" escalation already catches, at the price of some local-model time. Revisit if a stale ticket really happens. (Clarified with the owner, 2026-10-08.)
- **D2. What the lead reads:** the files the seed is about, `git log` for recent work on them, and the cards in docs/milestones/ in every state, building and done included, not only idea, planning and ready.
- **D3. Done means drop, open means merge.** A seed already done is dropped (f6-17), not merged into a finished card. A seed a building card covers is merged into it: `merge` already accepts any card (`cards` in `runner/planner.py`), so the runner doesn't change, only the prompt.

## Tickets
| # | id | who | diff. | depends on | what |
|---|----|-----|-------|------------|------|
| 01 | still-needed | L | 2 | – | The planner's prompt checks a seed is still needed before answering |
