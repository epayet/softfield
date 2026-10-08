# Milestone F49: don't ask me to merge conversations, just do it and keep context from both in a smart way

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
(or make a new one with information from all)

## Expected outcome
When the lead finds that a card repeats another, it merges them itself, straight away, with no Approve button. The kept card holds the owner's words from both cards, word for word, plus a short summary by the lead of what the duplicate's thread said. The kept thread's next answer knows that conversation. The owner sees a line on both threads saying what was merged and why, and can undo a wrong merge by saying so on the kept thread.

## Done when
- A planner reply with a `merge` whose duplicate is an idea card, or a planning card with no tickets, is applied in the same job: one commit on main, `F44 merged into F41 by the lead`. The owner is never asked to approve it.
- The kept card's notes hold the duplicate's notes as they were, and under them the lead's summary of the duplicate's thread (what was asked, what was answered, what is still open).
- The duplicate's whole thread is exported to `docs/planning/<its full key>.md` in that commit, so nothing from it is lost.
- The kept thread gets a lead line: "Merged F44 here: <the summary>", and its next planner job reads the duplicate's history, even when it resumes a session.
- A merge the runner can't apply on its own (the duplicate has tickets, or drafts on its plan branch) is left as a proposal, as today.

## How to test it
Plant two ideas that say the same thing ("the try again button does nothing" and "try again and dismiss don't work"), and talk on one of them a little. Send a message on the other. Once the lead answers: one card is gone from the board, the other's doc has both notes and a "What was said" summary, `docs/planning/` has the gone card's thread, both threads say what happened, and the desk shows no merge to approve. Then say "that wasn't a repeat, split it back" on the kept thread: the lead's reply proposes a `seed` that plants it again with its notes.

## Decisions
- **D1 Merges apply at once** (owner, 2026-10-08; replaces F6 f6-12's "approval closes one"): after a planner job, the runner applies each `merge` in its reply with the existing `_merge` and `_merged` steps (`runner/requests.py`), in one commit on main authored by the lead, before the reply is stored. The proposal is stored already settled (`merged`), so the desk shows no button and F31's archiving counts it as done. Only main's docs change (a card's notes, a removed card doc, the thread's export); nothing is queued, so "nothing is queued without the owner's approval" still holds.
- **D2 Which card is kept:** the more advanced one (ready over planning over idea), else the older one. The lead says so in the merge's `into`; the runner refuses, and leaves as a proposal, a merge whose duplicate has tickets in `tasks/` or drafts on `plan/<card>` (they would lose their milestone).
- **D3 Smart context, the owner's words kept whole:** a `merge` carries a new `summary` field: the lead's few lines on what the duplicate's thread said. The kept card gets, under "### From F44: <title> (merged by the lead on <date>)", the duplicate's notes verbatim (as today), then "What was said on F44's thread:" and the summary. The lead never rewrites the owner's notes: summarising is where a smart merge could lose what the owner meant, so the original words always stay beside it.
- **D4 The duplicate's thread is kept:** exported to `docs/planning/` (as `_export` does on approval, f20 D2) and its history (`planner.history`) added to the kept thread's next planner prompt, once, as "From F44's thread, merged here:". The duplicate's thread then points to the kept one, as today.
- **D5 No new card from both** (the owner's "or make a new one"): a new card means a new key, so links, tickets, branches and the board's place of the kept card would all change, for the same result. Merging into the kept card already holds all the information.
- **D6 Undo by asking:** no Undo button. A wrong merge is undone by telling the lead on the kept thread; it proposes a `seed` that plants the card again with its notes and summary, from the merge commit. Merges should be rare and visible enough that a button isn't worth its ticket.

## Tickets
| # | Ticket | Agent | Difficulty | Depends on | What |
|---|---|---|---|---|---|
| 01 | auto-merge | lead | 7 | f31-01 | D1, D2: the runner applies a reply's merges after the planner job; the prompt says so |
| 02 | merge-context | lead | 6 | 01 | D3, D4: the `summary` field, the export, the kept thread's line and its next prompt |
