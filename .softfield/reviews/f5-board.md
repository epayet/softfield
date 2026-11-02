# Review: F5, steer from the phone, and the board

- **Status:** done, signed off by the owner on 2026-10-23.

## Sign-off sheet

### 1. What changed
You can run the factory from your phone on the home Wi-Fi. The dashboard (`--lan`) answers on this machine's home address, and its buttons send requests the runner carries out at its next pick, as its console commands would: sign off a ripe milestone (on its planning page and on its own page), switch Claude's reserve, queue a set-aside ticket, and pause after this job / resume. While a dashboard page is open, the browser tells you when something new needs you and when all the work is done.

The **Board** tab replaced Milestones: every card and every bug on one field, from seed to harvested, with a search and a kind filter. A card's page shows its stage, where it sits in the line and its tickets in run order. Bugs are tickets of their own (`bug-…`), outside any card. Your old backlog is now 43 of them (bug-05 to bug-47), set aside in the Seed column for you to queue. Only what needs a decision or is waiting on something stayed in the backlog, each with its reason. The Tickets page's Set aside table lists them in the order they'd run, each with a Queue button.

### 2. How to test it yourself
1. On your phone, on the home Wi-Fi, open the dashboard's home address. The Board tab is there and Milestones is gone.
2. Open the Board. The Seed column holds the bug cards bug-05 to bug-47, each saying "Set aside, won't run until you queue it ›". Type "review" in the search: only cards with that word stay. Pick Bugs in the kind filter: only bugs stay.
3. Open Tickets. The Set aside table lists the same bugs in order, with a Queue column. Press Queue on one. The button greys out and "Asked: the runner will do it." shows in that row. After the runner's next pick the row says it's queued, and the ticket's card moves to Planted on the Board.
4. In the top bar, press ⏸ ("Pause after this job"). The runner finishes its job, then holds; ▶ ("Resume") starts it again.
5. The bar at the foot of the page asks "Get a notification when something needs you, or when all the work is done?": press Yes and allow it (on the phone's home address it shows the steps to let Chrome trust it first). The next item under Needs you shows a notification.
6. When this review's milestone is ripe, open F5's page from the Board: its Sign off button is the same as on its planning page.

### 3. Left for later
- **bug-05 to bug-47** in `.softfield/tasks/later/`: the old backlog as tickets, factory first, should-fix first. Queue the ones you want, or drag them on the board.
- `docs/backlog.md` keeps what waits on something (a hold no one uses yet, a browser test on the real server, a markdown renderer) and the decisions (several local developers at once; the product name, once product work resumes).
- **F173** (ready) makes the board's order the only order. Until it merges, a feature ticket's own `priority:` still beats its card's place. f5-13 is one of the tickets it strips.
- f5-10 (the 5-hour buttons) stays set aside: F8's reserve switch replaced it.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-04 ([1857](../sessions/2026-10-04-1857.md), [2203](../sessions/2026-10-04-2203.md), [2221](../sessions/2026-10-04-2221.md), [2233](../sessions/2026-10-04-2233.md), [2249](../sessions/2026-10-04-2249.md)): f5-01 to f5-06, the requests, the route, `--lan`, cards, bug tickets and the priority pick, all built by Claude as lead tickets, first time.
- 2026-10-06/07 ([2342](../sessions/2026-10-06-2342.md), [0051](../sessions/2026-10-07-0051.md)): f5-12 notifications and f5-18 pause, lead tickets.
- 2026-10-13 ([0012](../sessions/2026-10-13-0012.md)): f5-07 replan, then the board (f5-15, 16, 17) by the lead. f5-09 (Queue button) by the local model, first attempt. f5-08 (Sign off button) and f3-08 (field cards) failed three local attempts each and were finished by the lead's escalation.
- 2026-10-16 ([1543](../sessions/2026-10-16-1543.md)): f5-11 (Set aside by priority), local model, first attempt.
- 2026-10-23 ([0559](../sessions/2026-10-23-0559.md)): f5-13, the backlog into bug tickets, lead.
- Lessons:
  - **The replan paid off.** By f5-07 (2026-10-13), F6, F8, F31 and F50 had moved the ground under F5's plan. It found f5-11 already built (rewritten), the 5-hour buttons replaced, and a sign-off rule that would have offered a sign-off before the review. The board's tickets went straight through after it.
  - **Small, one-template tickets suit the local model; tickets that touch two pages don't.** f5-09 and f5-11 passed first time. f5-08 (milestone page plus planning's sign-off rule, with an import cycle) stalled twice with no edit in 10 minutes, then timed out. f3-08 failed three times.
  - The checkpoint's three findings were all real but small: tests that couldn't fail where they claimed to check. The review fixed them itself.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** merge F173 next, so a drag on the board is the whole story; f5-13's bugs then line up purely by where you put them. Then go through the 43 new bug cards on the board once, from the phone: drag the few you care about to the top of Seed and queue them. Most are small and suit the local model. A drag-and-queue on the board itself (rather than on Tickets) would make that a one-page job; I'd plant it if you find yourself flipping between the two.

### 7. What clogged the factory line
- **Local attempts that never got going: about 2 h 10 min.** f5-08: two "no edit after 10 minutes" stops, then a 60-minute last attempt that timed out (00:41–02:03 on 2026-10-13), then a 25-minute escalation. f3-08: three failed 10-minute attempts and a 6-minute wait for its direction (03:56–04:35), then an 18-minute escalation. Unclog: since the replan the lead routes tickets that span two pages to itself. f5-08 was marked for a developer only because "a button" looked small. The ticket-writing rule in `docs/task-writing.md` (one page, one function, an example to copy) covers it.
- **The card waited, by your order, not for lack of work.** The board tickets waited on f5-07's replan from 2026-10-07 to 2026-10-12, while F6, F8 and F9 ran above them on your priorities. f5-13 was put to priority 3 on 2026-10-12 and ran on 2026-10-23. f5-11 waited for f9-05 (same table) until 2026-10-16. Nothing sat idle meanwhile. Nothing to unclog: that's the board's order working.
- **One false start each:** f5-03 was interrupted after 12 s on 2026-10-04 (the runner was stopped) and f5-07 failed in 11 s on 2026-10-12. Each ran clean on its next pick.

## What was built
- **Requests (f5-01, 02, 18; F15's reorder since):** the `owner_requests` table (`_V5`); `runner/requests.py` `apply_requests` at each pick, while waiting, and at each command's start; `POST /requests`, the dashboard's only write, guarded by `HX-Request` plus a same-origin `Origin`/`Referer` (403 otherwise; an unknown kind is 400), answered by the polling `_partials/request.html`. Pause and resume change `state.json`, and the runner holds after its job.
- **`--lan` (f5-03):** binds to the machine's home address, behind `TrustedHostMiddleware`.
- **Cards and bugs (f5-04, 05, 06):** a card's state, priority and area in its doc header, synced to `milestones` (`_V6`); `bug-` tickets with `milestone: bugs` and `tickets.area` (`_V7`); `pick_next` by `run_order`.
- **Notifications (f5-12):** `static/notify.js`, per-project memory in `localStorage`. F12 has since replaced its "Notify me" button with the permission bar and added the service worker.
- **The board (f5-15, 16, 17; f3-08):** `factory_dashboard/board.py` derives each card's stage (D4) from its thread and tickets; `/board`; a milestone's page as its card; the line's field from the same cards.
- **Buttons (f5-08, 09, 11):** Sign off on a ripe milestone's page; Queue on each set-aside ticket; the Set aside table in run order with each priority.
- **The backlog (f5-13):** 43 bug tickets in `.softfield/tasks/later/`. Five items were dropped as already done, and each item that stayed in `docs/backlog.md` says why.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | nit | claude | The "own row" Queue test found the answer div anywhere in the section (checkpoint C800-2) | Fixed: the answer sits in the row's Queue cell, and the test checks it there and checks the button's target |
| F2 | nit | claude | Queue and answer cells had no column header (C800-3) | Fixed: one Queue cell with its header |
| F3 | nit | claude | Two priority tests passed if their row was missing (C1009-1) | Fixed: each reads its row by id |
| F4 | nit | claude | `later_priority_rows` could pair one row's id with the next row's priority | Fixed: reads each row with `later_row` |
| F5 | nit | claude | The Set aside heading named a repo path | Fixed: "tickets that won't run until you queue them" |
| F6 | nit | claude | The card's D4 still listed Growing as its own stage (F154 merged it) | Fixed in the card doc |

Checkpoint verdicts: all three findings confirmed. F4 was missed by the checkpoint that read f5-11's diff. Score: 8/10. The milestone delivers its whole Outcome, and its lead work held up under seven later cards that built on it. Points off for f5-08's misrouted ticket (an hour and a half of local attempts that never started) and for tests on two developer tickets that couldn't fail where they said they checked.

Checked and fine:
- the request guard (a site open in the browser can't post: no `HX-Request`, or another origin);
- a queue's subject only ever names a ticket in `later/` or `blocked/` (`find_ticket` globs that folder);
- every f5-13 ticket I sampled passes `check-tickets`, and the two delete tickets (bug-43, bug-44) carry their `rm` in `commands:`, as a headless lead job needs;
- the edited existing tests (f5-09's and f5-11's in `test_tickets.py`, f5-12's and f5-17's in `test_overview.py` and `test_app.py`) only added assertions or followed the tab change.

With the review's fixes, `tests/factory_dashboard` passes (909) and ruff is clean on the changed test. `tests/runner` (nothing of it changed here) passed in a combined run that was stopped at the call's time limit, about 75% through, with no failure.

The French: no `coucou/locale/fr/` change in this milestone (the product lives in its own repo since ADR 30).

## Backlog
Nothing added. f5-13 emptied it into bug tickets.

## Factory
- **Flow:** 18 tickets over 19 days, mostly waiting by your order behind F6, F8 and F9. No stop for you, no limit waits, no parks. Two escalations (f5-08, f3-08), both finished by the lead on their branches. One checkpoint ran; its three nits are fixed here.
- **Models:** Claude (Opus) built 13 lead tickets, first time each, including the replan. The local model passed 2 of 4 developer tickets first time (f5-09, f5-11) and failed 2 (f5-08, f3-08). The numbers and dollars are in the runner's report below.
- **What worked:** the replan (f5-07) before the board's tickets. It caught three stale tickets that would have cost developer runs or built the wrong rule.
- **What to change:** a ticket whose change spans a second page's rule (f5-08 reused planning's sign-off rule across an import cycle) goes to the lead, however small its diff. That's already `owner.md`'s "who builds what"; the replan should have applied it to 08 as it did to 15–17. No new rule needed. The checkpoint missed a regex that spans rows (F4). That's the same family as the vacuous `if`-loop it did catch, and bug-45 to bug-47 cover the older ones.

<!-- runner report -->
<!-- /runner report -->
