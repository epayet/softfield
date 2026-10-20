# Milestone F112: Plain words for "replan"

> **State:** ready · **Priority:** 7 · **Area:** factory
> Planned with the owner on 2026-10-13, in a terminal session.

## Notes
The owner (2026-10-13): "explain what current replan is, is this internal terminology? … is it clear what a replan is?"

## Expected outcome
The dashboard never shows the bare word "replan". A proposal that changes tickets already in the queue is called "Change to queued tickets" and says how many it changes; the lead's own check ticket in the queue is called a "plan check".

## Done when
- On a thread and on its review page, a replan proposal reads "Change to queued tickets", with what it changes ("2 changed, 1 added, 1 set aside").
- In Next in line, a ticket such as `f15-05-replan` is followed by "plan check".
- To test: open a card with a replan proposal on the phone and check no label says "replan"; open the Overview while a `…-replan` ticket is queued.

## Decisions
- **D1 The word was ours, with two meanings.** In the planning room a `replan` is a proposal that edits, adds or sets aside tickets of a card already in the queue (F6 D2, f6-13). In the queue a `…-replan` ticket is the lead checking a card's decisions and remaining tickets against what was built (ADR 16 item 7). Neither was explained on a page.
- **D2 Only the words on the pages change.** The proposal kind stays `replan` in the runner, the database and the planner's brief, and ticket ids stay as they are.
- **D3 "Refresh against main" is a third thing** (F73 D6): rechecking a draft nobody has approved yet. It keeps its own name.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | replan-in-plain-words | D | 3 | – | D1, D2: the labels on the thread, the review page, the desk and Next in line |
