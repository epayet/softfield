# F75 review: a thread shows it's archiving once its last proposal is approved or rejected

- **Status:** done, signed off by the owner on 2026-11-13.

## Sign-off sheet

### 1. What changed
- When your Approve or Reject settles the last open proposal of the lead's latest reply, that thread's box in "Your answers wanted" turns dashed orange straight away, says "archiving at the runner's next pick", and stops counting as waiting for you. Until now only the proposal was dashed.
- The thread's own page shows "Archiving at the runner's next pick" in place of the Archive button, the same mark a manual Archive shows.
- If another proposal of the same reply is still open, the thread stays solid, because the runner won't archive it.
- Rejecting a plan also counts the reply's other drafts (an ADR, a mock-up) as leaving, since the runner drops the plan branch with them.
- If the runner refuses your approval, the thread goes solid and counted again on the next refresh.

No mock-up or after pictures for this card.

### 2. How to test it yourself
1. On your phone, open `/planning` and pick a thread whose latest reply proposes only a plan. Press Approve on it.
2. Right away, check that the proposal and the thread's box are both dashed orange, that the box says "archiving at the runner's next pick", and that the Planning tab's count has dropped by one.
3. Open that thread: it shows "Archiving at the runner's next pick" and no Archive button.
4. On a thread whose reply has two open proposals, approve only one: its box stays solid and still counts.
5. After the runner's next pick, the first thread is listed under Archived as approved.

### 3. Left for later
- Nothing set aside. Three small notes are in the findings below; none is worth a run.

### 4. Decisions waiting for you
- None.

### 5. How the work went
- 2026-11-12 (session [2026-11-12-0628](../sessions/2026-11-12-0628.md)): one ticket, `f75-01-archiving-on-approval`, merged on its first attempt by headless Claude (Sonnet), 188 lines with 7 new tests and no existing test changed.
- Lessons:
  - The card's "Why it happens" section, read from the code, named the exact functions (`_close_if_settled`, `_acted_on`, `proposal_state`). The ticket landed the rule correctly on its first attempt.
  - The card planned this as a developer ticket ("D"), but it ran as a lead ticket on Sonnet. It was cheap and clean, but the local model never got a ticket that followed an example closely. Nothing to change for one ticket; worth watching if it keeps happening.

### 6. What next
- **Product:** product work stays on hold (owner, 2026-10-04).
- **Factory:** the dashboard and the runner now each hold their own copy of "when does a thread close". If F31's rule changes again, put that rule in one shared function in `runner/planner.py` in the same change, so the dashed box can't promise an archive the runner won't do. Also check why a ticket planned for a developer ran as a lead ticket.

### 7. What clogged the factory line
- Nothing on this milestone: one ticket, one job, merged first time. The session's waits went to other cards (`f210-05` escalated) and are counted in their own reviews.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/planning.py`: `_closing(conn, project_id, card, known)` applies `_close_if_settled`'s rule to the thread's latest set: every proposal is approved, rejected, a merge that has left main, or on its way, and at least one is on its way (D1). A pending reject on a draft makes every open draft of the set count as on its way (D2). The desk passes the closing answer threads to `_acted_on`.
- `factory_dashboard/coming.py`: `_acted_on` takes `closing` and gives those threads the manual Archive's words and dashed look (D3).
- `factory_dashboard/thread.py`: the page shows the Archiving mark when `_closing` holds and no manual archive request is pending.
- I checked the rule against the runner: `_settles` closes threads after `approve_plan`, `accept_adr`, `reject` and a general-thread `plant`, which are exactly the requests `proposal_state` reads as on its way. Seeds only appear on the general thread, so the two can't disagree there.

## Findings and resolutions
All three are nits, recorded here only:
- **F1** (`planning.py:321`): `_closing` keeps its own copy of `_close_if_settled`'s rule and imports the runner's private `_latest`. They agree today. Suggested fix: if the rule changes again, move it into one shared function in `runner/planner.py` (see "What next").
- **F2** (`planning.py:676`): the desk reloads every owner request once per answer box and lists the cards twice. Fine at today's sizes. Suggested fix: fold the two reads into one if the desk gets slow.
- **F3** (tests): no test for a merge whose card has left main counting as settled, and none for a pending manual Unarchive taking precedence on the page. Both paths are a few lines and read right.

No checkpoint findings to judge. Score: 8/10. Correct, close to the card, well tested. Points off for the copied rule and the private import.

French: nothing in `coucou/locale/fr/` changed.

## Workflow observations
- The card's code-reading paid off: one attempt, no fix rounds.
- The ticket table says `kind: lead`, while the card's table said "D". If the planner now routes small factory tickets to Claude on purpose, the card template's "Who" column is out of date. If not, it's a routing slip to look at.
