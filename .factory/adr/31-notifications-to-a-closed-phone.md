# ADR 31: Notifications to a closed phone, through ntfy

- **Status:** Accepted (by the owner, 2026-10-16)
- **Date:** 2026-10-16
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 26](26-notifications-on-the-home-wifi.md), its Consequences ("the ntfy app on the phone… a later card") and [ADR 18](18-dashboard-writes.md) item 4 ("push to a closed page is in the roadmap").
- **Evidence:** F142, the owner (2026-10-16): "Why am I not getting notifications on my phone anymore". On 2026-10-15 six items were raised on Softfield (two stopped reviews, two lead replies on F135, two sign-offs), spread from 00:23 to 21:47. A browser notifies only from a dashboard page open in front: Chrome freezes a background page within minutes, and a page that comes back after 60 s takes what it finds as known (`FRESH` in `factory_dashboard/static/notify.js`). F114 (Notifications only for what needs me) left this gap out and said it starts as an ADR.

## Context
- The owner checks the factory from a phone; a notification is worth most when the phone is in a pocket, which is exactly when none comes.
- **ntfy** is an open-source notification service. A program sends a message with one web request to `https://ntfy.sh/<topic>`; the ntfy app on the phone, subscribed to that topic, shows it at once, screen off, browser closed. A message can carry a title, a body and an address the tap opens.
- The Play Store app gets ntfy.sh's messages through Google's own push channel, so it costs no battery of its own.
- Everything that needs the owner and isn't seen by the dashboard alone is stored by the runner, at three places: a review's verdict (`_record_items` in `runner/owner.py`), a lead's reply (`run_planner` in `runner/loop.py`) and Claude's reserve switch going off (`runner/requests.py`), each through `metrics.upsert_owner_item`.

## Decisions (draft; ⚑ = deviates from an earlier decision)
1. **⚑ One notification per thing that needs you, through the public ntfy.sh, opening its page.** It says what kind of thing it is and which project, never a card's title, a reply or a test step: "softfield · The lead answered you", "softfield · A card is ready for your sign-off", "softfield · A review stopped", "softfield · A ticket needs your decision", "softfield · Claude's reserve: your choice". A tap opens the page where you act: the card's thread (`/planning/<card>?project=…`) for a reply, a sign-off or a stopped review, the Overview for the rest. The page opens only on the home Wi-Fi, as the dashboard does today.
2. **Several things raised in one go are one notification.** A review's verdict can raise three items about one card at once; they come as one ("softfield · 3 things need you on one card"), opening that card. Everything else comes one by one.
3. **⚑ The runner sends it, at the moment it stores the item.** No loop and no memory of what was sent: the runner sends right after `upsert_owner_item`, from a new `runner/notify.py`, when the item is new or opens again; a lead's reply always sends, since each reply is news. The sending is best-effort: a 5-second limit, and a failure is a line in the run's report, never a failed job. What only the dashboard sees (a runner that stopped mid-job, tickets waiting with no runner) doesn't reach the phone: a dead runner can't send, and systemd restarts it anyway.
4. **⚑ One `notify`, two channels: the browser and the phone.** `notify(conn, project, thing)` in `runner/notify.py` stores each notification once, as a row of a new `notifications` table (id, project, time, kind, card, title, body, link), then posts it to ntfy when the setting is there. The browser shows the same rows: the `/live` look carries those newer than the last one the page saw, every project's, and the page shows each once (several at once: one "N things need you", opening the desk). Nothing else decides what notifies. The two differ only in words: the browser's title names the card (F114 D1's table, which moves into `runner/notify.py`); ntfy's never does (item 1). A browser that comes back from sleep shows what it missed as one notification, where today it drops it. Each device chooses its channels: block the dashboard in the browser, or don't install the app. "All work done" is a `notify` too, sent by the runner when the queue empties; only what the dashboard alone sees (a runner stopped mid-job, tickets waiting with no runner) stays the page's own check, as today. This replaces F114 D1's `notices` worded in the dashboard from open items, and the per-look comparison of ids in `notify.js`.
5. **The topic lives in the machine's settings, not the repo.** `~/.config/softfield/factory.toml` gets `[notify] ntfy = "https://ntfy.sh/<topic>"`. `softfield notify setup` writes it once with a long random topic and prints the topic to type in the app; `softfield notify test` sends one notification. No setting, no sending.
6. **No Docker.** Nothing new runs on this machine.
7. **Unchanged:** what needs the owner (F114), browser notifications kept beside ntfy, with their titles and their tap to the page (F114 D3), the dashboard on the home Wi-Fi only, no tunnel, no public host.

## Settled with the owner
1. **The public ntfy.sh, free, to begin with** (owner, 2026-10-16). A server of our own stays the next step if ntfy.sh's limits or privacy ever matter; only the address in the setting changes.
2. **One notification per thing, opening its page** (owner, 2026-10-16), not a count: item 1.
3. **Sent from where it happens, not by a loop** (owner, 2026-10-16): item 3.
4. **The topic outside the repo**: item 5, kept after the owner asked why (the topic is the only lock, and since ADR 30 it is the machine's, not a project's).
5. **Both channels, from one `notify`** (owner, 2026-10-16: "it should do both and clients can decide which one they want to use"): item 4.

## Cost and risk
- ntfy.sh sees each notification's kind, project name, time and the dashboard's home address (a private address, useless outside the home). Anyone who learns the topic can read them and send fake ones; the fix is `softfield notify setup` again and the new topic in the app.
- ntfy.sh limits a free sender's messages. The busiest day so far raised about twenty items (2026-10-13), far below its free daily allowance; if a limit is hit, the rest of that day's notifications are lost and the desk still holds them.
- A second notification on the phone when the dashboard is also open in front there: turn the dashboard's off in Chrome's site settings on the phone.

## Consequences
- F142 gets three tickets: `notify`, its table, the ntfy post, the setting and the two commands (f142-02, the lead's: stored data and a request leaving the machine); the browser reading the rows (f142-01, a developer's, after F114 has landed); the phone's steps and `softfield doctor`'s check (f142-03, a developer's).
- F114 (Notifications only for what needs me) lands first as planned; f142-01 then moves its wording from `notices` in `factory_dashboard/overview.py` into `runner/notify.py` and reuses its tap (`sw.js`, the link in the notification's data). Its one-per-look rule becomes one per `notify` call.
