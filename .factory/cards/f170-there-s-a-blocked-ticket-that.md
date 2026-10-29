# Milestone F170: Blocked tickets: give the tests 30 minutes, and put the lead's fix on the desk

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-21.

## Notes
There's a blocked ticket that I keep trying to approve and it keeps coming back I don't get it. What am I supposed to do with this, why doesn't it just work

### From F190: A blocked ticket doesn't link back to the milestone /… (merged by the lead on 2026-10-29)
A blocked ticket doesn't link back to the milestone / original discussion and plans so the current blocked ticket f21 atm looks like I can't do anything about it

## What happened (2026-10-21)
- **One cause, two tickets.** The full test suite takes 1100 to 1170 s and the gate stops it at 1200 s (`[timeouts] gate` in `.factory/project.toml`). f132-01 (blocked 15:56) and f152-01 (blocked 22:25) had good work, cut on that limit three times each. Each cost about 3.5 h of the line and about $2 of Opus (direction and escalation), plus the lead's look. f15-09 was cut the same way on 2026-10-20 and passed only on its last attempt.
- **The escalations couldn't fix it.** Each raised the limit on its ticket's branch, but the runner reads a project's config at the session's start and keeps it, so neither the branch nor a raise merged to main reaches it before a restart.
- **Try again ran it unchanged, and then the fix couldn't land.** The lead's fix for f132-01 (F132's replan, with f132-09 raising the limit) waited on F132's thread. The desk's yellow button was Try again: at 21:23 it put f132-01 back in ready/ as it was (it will hit the same limit). At 21:46 F132's Approve was refused, "plan/f132 clashes with main", because Try again had already put the same file there. f152-01's fix then leaned on f132-09, which lives on that refused branch, so it can't be approved either.

## Decisions
- **D1: overtaken by F71 the same night** (lead, 2026-10-21): the suite runs on 16 workers, and check-all takes 4.5 minutes instead of 19.6, so no limit is raised. f170-01, f132-09 and f152-03 are dropped.
- **D2: Try again never makes the lead's fix unapprovable** (f170-02): approving a replan whose ticket Try again already put back replaces that ticket with the lead's version, footers carried over.
- **D3: the desk offers the lead's fix as its yellow button** (f170-03, mock-up `.factory/cards/f170-mockup/blocked-on-the-desk.html`): the fix's first point and title in the blocked item, "Approve the lead's fix" right there, "Try again as it is" quiet beside it with what it does. A bug ticket keeps today's two buttons.
- **f132-01 and f152-01:** their escalations' work was landed from their branches by the lead in a terminal session (2026-10-21), check-all passing on workers. F132's and F152's replans are overtaken.

## Tickets
- f170-02-fix-after-try-again (lead)
- f170-03-desk-offers-the-fix (developer)
