# Milestone F142: Phone notifications: every project, and with the dashboard closed

> **State:** done · **Priority:** 1 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-29. Base: git tag `f142-why-am-i-not-getting-notifications-start`. Report: [`.factory/reviews/f142-why-am-i-not-getting-notifications.md`](../reviews/f142-why-am-i-not-getting-notifications.md).
> Planted by the owner on 2026-10-16.

## Notes
Why am I not getting notifications on my phone anymore

## What happens today (from the code and the database, 2026-10-16)
- **A notification follows the project the open page shows, and no other.** `notify.js` compares the `/live` facts of the page's `?project=` (`_live_context` in `factory_dashboard/overview.py`). Since ADR 30 (2026-10-14) one runner and one dashboard serve every project, so an item on Softfield while the open page shows another project never notifies.
- **The bare address opens on Travel-companion.** The dashboard service (`softfield dashboard --lan`, run outside any project) opens on the first project in the owner's order (`_machine_command` in `runner/cli.py`). Today that is `travel-companion` (order 1), which has no open item. A phone bookmark without `?project=softfield` watches it.
- **The runner did raise items worth a notification on Softfield:** on 2026-10-15, two stopped reviews (F19 at 00:23, F28 at 07:35), the lead's replies on F135 (08:40, 11:37), and two sign-offs (F109 at 16:36, F95 at 21:47). Each was a new id, so a page on Softfield, open and in front, would have notified.
- **On a phone, only an open page in front notifies** (ADR 26, Context): Chrome freezes a page in the background within minutes, and a page that comes back after more than 60 s takes what it finds as already known (`FRESH` in `notify.js`). Whatever arrives while the dashboard is closed or in the background never notifies. This hasn't changed since F12.
- Not the cause: the 5-second look still runs on every page (`#live-poll` in `base.html`, `#live-needs-you` on the Overview since f19-02), and the port is still 8765.

## Expected outcome
- A dashboard page open on any project notifies for an item on every project, named with its project when it isn't the page's.
- With the dashboard closed, the phone's ntfy app shows one notification per thing that needs the owner, saying its kind and project, and a tap opens the page where they act ([ADR 31](../adr/31-notifications-to-a-closed-phone.md)).

## Done when
- f142-01, f142-02 and f142-03 merged.
- To test the page: open the dashboard on Travel-companion's Overview, allow notifications, and send a message on any Softfield card. When the lead replies, a notification comes, its title starting "softfield:", and a tap opens the Softfield card's thread.
- To test the phone: follow `docs/notifications-on-the-phone.md`, close the dashboard, lock the phone, and send a message on a Softfield card from the desktop. When the lead replies, the phone shows "softfield · The lead answered you"; on the home Wi-Fi a tap opens that card's thread.

## Decisions
- **D1: one look, every project.** `_live_context` adds to the page's own notices (F114, Notifications only for what needs me, as built) the open stored items (`owner_items`) of every other project in `metrics.projects_in_order`. The dashboard's own needs (a runner stopped mid-job, an idle queue) and "All work done" stay the page's project's.
- **D2: an id names its project** (`softfield/owner-129`), so what a browser saw is one set for the dashboard (`notify:seen`), not one per project: moving between projects neither notifies again nor misses.
- **D3: nothing stored twice** (ADR 31 item 4, amended at the owner's word, 2026-10-19). The owner item is the one record; the runner sends it to ntfy the moment it stores it, and the browser notices it on its next look. No `notifications` table.
- **D4: the phone, as ADR 31 decides.** The topic is in the machine's `~/.config/softfield/factory.toml`; `softfield notify setup` and `softfield notify test` are the two commands the phone's steps name.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | notify-every-project | D | 3 | f114-07, f114-08, f114-09 | D1, D2 |
| 02 | ntfy-sender | L | 4 | – | the ntfy send straight away, the setting and two commands (ADR 31 items 1–5) |
| 03 | phone-steps | D | 2 | 02 | the phone's steps in `docs/`, `doctor`'s check |

01 waits for F114's three fix tickets still ready, which change the same `notify.js` and tests. 02 is the lead's: a request leaving the machine from the runner.

No mock-up: no dashboard page changes, only the notifications' words.
