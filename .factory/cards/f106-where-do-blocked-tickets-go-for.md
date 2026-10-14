# Milestone F106: where do blocked tickets go for me to review

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-12.

## Notes
where do blocked tickets go for me to review

## Expected outcome
- A blocked ticket shows on the owner's desk and in the Overview's "Needs you" the moment the runner blocks it, with its reason in plain words, what waits behind it, and the lead's suggested fix.
- The owner answers it from the dashboard: try again, take the lead's fix, or set it aside. No terminal, no reading of branches.
- It leaves the desk as soon as the owner has acted.

## What happens today (from the code, 2026-10-12)
- **Where they go:** `block` in `runner/loop.py` moves the ticket to `.factory/tasks/blocked/` with a `reason:` footer and commits; its work stays on the branch `task/<id>`; the tickets that depend on it pause.
- **Where the owner sees them:** only in the "while you were away" line on the Overview (a link per blocked ticket) and on `/tickets` with "blocked" typed in the State box. The desk on `/planning` has no group for them (`desk` in `factory_dashboard/planning.py`).
- **"Needs you" misses them under `runner run`:** a blocked ticket becomes a "Needs you" item only when `verdict` in `runner/owner.py` runs, which `runner milestone` does at its end and `runner run` does only after a review. `block` itself stores nothing.
- **Nothing brings one back:** no command or button moves a ticket out of `.factory/tasks/blocked/`. The item's command (`uv run runner milestone <key>`) reruns the milestone and skips the blocked ticket again; `runner queue` only takes tickets from `.factory/tasks/later/`.
- **Four wait there now,** all the lead's own tickets, none shown as needing the owner: `f21-01-planner-sees-the-plan`, `f21-02-sections-in-prompts` and `f31-03-point-outcomes` (check-all failed, work kept on their branches) and `f21-03-trim-owner` (the lead changed nothing).
- **What happened on 2026-10-12** (terminal session): the three "check-all failed" ones, and f48-01 after them, had finished their work. A scratch file on main (`tests/factory_dashboard/test_probe_tmp.py`, from the F12 review) failed the `layout` gate for every ticket, and the ticket that removed it (f12-03) was at priority 100, behind them. The file was removed and the four were landed from their branches by hand; f21-03 was requeued with a limit it can meet. D5 is so this can't repeat.

## Decisions
- **D1 Blocked tickets get a desk group, "Blocked tickets", at once:** `block` stores an owner item (kind `blocked`, subject the ticket, text "<id> blocked: <reason>", plus " · N tickets wait behind it" when some do). The desk's second group, after "Didn't go through", lists each open one, linking to its ticket's page. The Overview's Needs you counts them through the desk's entry only, as F95 D1 does for sign-offs.
- **D2 The lead looks first, the owner decides** ([ADR 29](../adr/29-the-lead-looks-at-a-blocked-ticket.md), Proposed): when a ticket is blocked, the runner queues a planner job on its card's thread, with a message of the runner's own. The lead reads the branch and the logs and replies with what went wrong and a fix as a `replan`, which may bring the card's blocked ticket back (reworked into `.factory/tasks/ready/`, or to `.factory/tasks/later/`). One look each time a ticket is blocked; none for a bug ticket, which has no card.
- **D3 Two buttons on the item:** "Try again" is a `queue` request, which now also takes a ticket from `.factory/tasks/blocked/`; "Set aside" is a new request, `set_aside`, to `.factory/tasks/later/`. Both resolve the item, are applied at the runner's next pick, and show on their way at once. Before a retry the runner copies the branch `task/<id>` to `blocked/<id>`: a lead ticket starts again from main, and its failed work must not be lost.
- **D4 The owner never reviews the code of a blocked ticket:** the item says what failed and what the lead suggests, in plain words. The branch and the logs are a link for the curious.
- **D5 A red main blocks nothing** ([ADR 29](../adr/29-the-lead-looks-at-a-blocked-ticket.md) item 7; added by the lead in a terminal session, 2026-10-12): when a lead ticket's checks fail only where main fails too, the ticket isn't blocked. Its work waits on its branch, the run takes no other lead ticket, and one "Needs you" item says which check fails on main and which ticket would fix it. Developer tickets go on.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | blocked-reaches-the-owner | L | 6 | – | D1, D3: `block` stores the item; the two requests (runner is protected) |
| 02 | blocked-on-the-desk | D | 4 | f12-03, f95-01 | D1: the desk group, counted once on the Overview |
| 03 | try-again-set-aside | D | 5 | 01, 02 | D3: the two buttons, and on its way |
| 04 | lead-looks-at-a-block | L | 7 | 01, 06 | D2: the look (ADR 29 items 1, 2, 4–6) |
| 05 | replan-brings-back-blocked | L | 6 | 04 | D2: a replan may rework a blocked ticket (ADR 29 item 3) |
| 06 | red-main-blocks-nothing | L | 6 | 01 | D5: a check failing on main too stops the lead's tickets once, and blocks none (ADR 29 item 7) |

02 needs nothing of the lead's, so the line has a developer ticket to run beside the lead's chain. 04, 05 and 06 wait for ADR 29. 06 goes before 04 (owner, 2026-10-12): with main failing, each blocked ticket would otherwise cost a look.

## Done when
- Block a ticket (a lead ticket whose check-all fails): within a page refresh it is on the desk under "Blocked tickets", counted in the Overview's "Needs you" through the desk's entry, with its reason and what waits behind it.
- The lead's reply appears on the card's thread with a fix to approve.
- Press "Try again": the item shows as on its way and leaves the desk; at the runner's next pick the ticket is back in the queue.
