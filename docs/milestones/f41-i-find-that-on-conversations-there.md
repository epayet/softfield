# Milestone F41: I find that on conversations, there is the raw text and then small boxes to review each point. the information is not…

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-08. Base: git tag `f41-i-find-that-on-conversations-there-start`. Report: [`docs/reviews/f41-i-find-that-on-conversations-there.md`](../reviews/f41-i-find-that-on-conversations-there.md).
> Planted by the owner on 2026-10-08.

## Notes
I find that on conversations, there is the raw text and then small boxes to review each point. the information is not exactly the same and the most interesting part are the boxes so i tend to just scroll down and ignore the raw text

how relevant is the raw text, and perhaps it should be hidden until i want to see it? like an accordion. focus is on the boxes and the decisions. This was on deskrop

### From F44: In proposal I don't need such information as 'i checked and there is no fuplicate' (merged by the owner on 2026-10-08)
Like this, I.have nothing to do with this information so it wastes my time: 

No duplicate
No other card or thread asks for this. F30 (newest answer first) and F16 (the 'your answer wanted' label) are also about the thread page, but they are separate issues.
→ Nothing.

## Outcome
- On a thread, the owner reads the lead's points and nothing else: the lead says everything once, in the points, and the free text, folded shut, is there only if they want it.

## Why the text and the boxes differ
The planner's prompt (`runner/prompts.py`, `_PLANNER_HEAD`) asks for "numbered points" in the reply, and its tail asks for the same points again in the `json` block. So the lead writes them twice: once as prose, once as boxes, and the two drift apart. The boxes are what the owner comments on and what the next round reads, so the boxes are the record.

## Decisions
- **D1 The points carry everything:** the prompt says the text before the `json` block is at most two short lines (what this reply does), or nothing; every answer, risk, question and ask (a pause, a choice) is a point. No point says that nothing was found (no repeat, no conflict): the owner has nothing to do with it (F44's ask).
- **D2 The text folds when there are points:** a lead message with points shows its text in a closed "Full reply" fold above the points; opened, it reads as today. Desktop and phone alike.
- **D3 No points, no fold:** a lead message without points (its `json` block missing or broken, a reply written outside a job) shows its text open, as today: it is all there is, and the note saying why the block wasn't read must be seen. Owner messages never fold.
- **D4 What doesn't change:** the proposal page, the point boxes and their comments, the deck on the phone, and the history the next planner job reads (it keeps the full text).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | points-carry-all | L | 2 | – | D1 (protected: `runner/`) |
| 02 | fold-the-text | D | 2 | – | D2, D3 |

## Not in this card
F30 (newest answer first) and F42 (the proposal card's small scroll area) are on the same pages but are separate asks.

## How to test
Open a thread whose last lead reply has points: the points come first under a one-line "Full reply" fold; open it and the text reads as before. Open a reply whose `json` block was broken: its text and note show open. Send a message on any card after 01 merges: the reply's text is two lines at most, and no point says "no duplicate".
