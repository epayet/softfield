# Review: F142, phone notifications from every project, and with the dashboard closed

- **Status:** review round 2 done (2026-10-28): both fix tickets merged and resolved; ready for your sign-off.

## Sign-off sheet

### 1. What changed
You get notifications again, and from every project. Two things changed:
- **With the dashboard open, on any project:** a page open on Travel-companion now notifies for Softfield too (and the other way round). A notice from another project starts with its name, for example "softfield: The lead replied: <the card's title>", and a tap opens that card on its own project. Moving between projects doesn't notify the same thing twice.
- **With the dashboard closed:** the runner sends each thing that needs you to the free **ntfy** app on your phone, the moment it stores it, screen off and browser closed. It says only the project and the kind of thing ("softfield · The lead answered you", "softfield · The lead looked at a blocked ticket", "softfield · The lead couldn't answer you", "softfield · A card is ready for your sign-off", "softfield · A review stopped", "softfield · A ticket needs your decision", "softfield · Claude's reserve: your choice"), never a card's title or a reply's words.
- **"All work done"** comes once per project, when that project's work ends, and never just because you moved to an idle project's page. Several things on one card at once are one notification. A tap opens the page where you act, on the home Wi-Fi.
- Nothing is sent until you set it up (below). `softfield doctor` says whether you have.

### 2. How to test it yourself
1. Set the phone up once, following [`docs/notifications-on-the-phone.md`](../../docs/notifications-on-the-phone.md): on the machine run `softfield notify setup`, subscribe to the topic it prints in the ntfy app, then run `softfield notify test`. "softfield · Notifications work" arrives within seconds.
2. In Chrome on the phone, turn off the dashboard's own notifications (the doc's "Nothing twice"), so each thing comes once.
3. Close the dashboard and lock the phone. From the computer, send a message on any Softfield card.
4. When the lead replies, the phone shows "softfield · The lead answered you". On the home Wi-Fi, a tap opens that card's conversation.
5. On the computer, with notifications allowed in its browser: open the dashboard on Travel-companion's Overview and leave it in front. Send a message on a Softfield card. When the lead replies, a notification titled "softfield: The lead replied: <the card's title>" comes, and a click opens the Softfield card's conversation.
6. While Softfield is busy, click between Travel-companion and Softfield a few times: nothing notifies, not even "All work done".
7. When a ticket gets blocked, the phone shows "A ticket needs your decision", then, after the runner's next pick, "The lead looked at a blocked ticket"; a tap opens the card's conversation with the lead's look.

### 3. Left for later
- Several notices bundled from different projects open the Planning room of the page's own project. Rare (two new things in one 5-second look); left as is.

### 4. Decisions waiting for you
None. ADR 31 (accepted, amended at your word on 2026-10-19) is now code.

### 5. How the work went
- 2026-10-16 to 10-19: planned in the Planning room over five planner jobs ($22.82), including ADR 31 and its amendment (nothing stored twice).
- 2026-10-23 02:09 ([session](../sessions/2026-10-23-0209.md)): `f142-02-ntfy-sender`, the lead's ticket (protected `runner/`), first attempt, 14 minutes, $3.22.
- 2026-10-23 02:28 ([session](../sessions/2026-10-23-0228.md)): `f142-03-phone-steps`, the lead's, first attempt, 5 minutes, $0.90.
- 2026-10-23 10:00 ([session](../sessions/2026-10-23-1000.md)): `f142-01-notify-every-project` by the local model, first attempt, 77 minutes; a checkpoint ($0.24) found the ids differed between a project's own page and the others'; fix ticket `f142-02-fix-own-project-ids-notify-twice`, local model, first attempt, 62 minutes. 9.9M local tokens for the two.
- 2026-10-23 12:52 ([session](../sessions/2026-10-23-1252.md)): `f142-04-fix-all-done-per-project` by the local model, first attempt, 37 minutes, 1.3M local tokens; its checkpoint ($0.17) passed it with one nit (a test gap, which the review filled).
- 2026-10-23 to 10-27 ([sessions](../sessions/2026-10-26-2252.md)): `f142-05-fix-a-look-is-not-an-answer` touches the protected `runner/`, so the lead takes it; it waited for Claude's weekly reserve, then was parked five times for Claude's limits, interrupted once, and merged on 2026-10-27 23:16 ([session](../sessions/2026-10-27-2312.md)), Sonnet, $0.79 over two jobs.
- 2026-10-28: review round 2 (this one): both fixes resolved; one test added, one duplicate mark removed.
- Lessons:
  - A review fix of about ten lines in protected code should be done by the review itself. I routed f142-05 to "local", the runner rightly handed it to the lead, and it then waited four days behind Claude's limits.
  - The checkpoint caught the id slip but not two others in the same diff: other projects' notices were worded without their cards' titles, and one "all done" flag was shared by every project. Its tests used an `adr` item, whose words don't depend on titles, so they couldn't see it. A worded notice is tested with a kind whose words come from the data.
  - Two of the developer's tests passed with nothing to check (an `if`-guarded assert, a "/ in the key" check any id passes). The review tightened them.
  - The lead's two tickets on the runner went in first time and needed only one small fix (F4).

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** now that both fixes are in, a week of ntfy will show whether the phone gets too much. If it does, the next step is quiet hours or a daily digest for the less urgent kinds (the reserve switch), which ADR 31 left out. I'd plant it only if you find yourself muting the app.

### 7. What clogged the factory line
- **Planning to building, 3½ days** (plan settled 2026-10-19 23:20, first ticket 2026-10-23 02:09). The plan needed ADR 31's amendment, then the card waited its turn behind cards above it on the board; the factory merged other cards' tickets meanwhile. Nothing to unclog: the board's order working.
- **f142-01 waited on F114's fix tickets** (f114-07 to f114-10, which changed the same `notify.js` and tests), by design, to avoid two branches on the same lines. F114's chain of six test fixes over six days (see its review) is what held it.
- **The local model's two tickets took 2 h 19 min** for about 30 lines of code; first attempts, no limit waits, no stops for you. The ids slip cost one extra hour (the fix ticket); a ticket listing the exact ids (`softfield/owner-129`, own project included) in Done when would have avoided it. It did say so in Context; the developer read "own project keeps its titles" as "keeps its ids".
- **f142-05 waited four days for a ten-line change** (ready 2026-10-23 14:15, merged 2026-10-27 23:16): it touches protected `runner/`, so only Claude may build it. First it waited for the weekly reserve (1–2% left until Mon 26 Oct 17:00), then it was parked five times for the 5-hour limit and interrupted once. What unclogs it: a review does such a fix itself, in the review job, while Claude is already running (lead.md's "protected code" rule; I misrouted it).

## What was built
- `runner/notify.py` (new): `send` posts one notification to the machine's `[notify] ntfy` address with a 5-second limit, never raises, and returns why it failed for the run's report. `item_message`/`items_message` choose the words and the page by the item's kind; `setup` writes the topic (24 random lowercase letters and digits) once, keeping the rest of the file.
- The three places that store an owner item send when it is new or opens again: `owner._record_items` (a verdict's items about one card, one notification), `loop.block` and `loop.run_planner` (every lead reply), and the reserve switch going off in `requests._lapse`. Nothing is stored about the sending; no table.
- `runner/config.py`: `machine_ntfy`, from the machine's file only. `runner/cli.py`: `softfield notify setup` and `softfield notify test`. `runner/setup.py`: `doctor` says whether notifications are set up (not needed to pass).
- `docs/notifications-on-the-phone.md`: the Android steps, what a notification says, nothing twice, a leaked topic.
- `factory_dashboard/overview.py`: every notice id names its project (`softfield/owner-129`); every other project's open items join `data-notices`, titled with the project's name. `static/notify.js`: one `notify:seen` key for the dashboard.

Edited existing tests: `test_data_notices_has_the_ids` expects the prefixed ids; `test_compare_uses_one_key_not_per_project` now really loads the other project's page (the checkpoint's point). Both are right.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | Other projects' notices were worded without their cards' titles or proposal counts ("softfield: The lead replied: f7") | Fixed: that project's titles and proposals; new test `test_another_projects_reply_is_worded_from_its_own_cards` |
| F2 | should-fix | local | One "all done" flag for every project: switching from a busy project's page to an idle one's says "All work done" | Resolved by `f142-04-fix-all-done-per-project` (round 2) |
| F3 | should-fix | local | A look at a blocked ticket and a failed reply both notify "The lead answered you"; the block's notification is untested | Resolved by `f142-05-fix-a-look-is-not-an-answer` (round 2) |
| F4 | nit | claude | `notify setup` on a `[notify]` with an empty `ntfy = ""` added a second key, leaving the machine's whole settings file unreadable | Fixed, with a test |
| F5 | nit | claude | `test_data_notices_ids_start_with_project_name` accepted any prefix; `test_data_notices_excludes_forgotten_project` passed with no notice | Fixed: exact ids, the own item present |
| F6 | nit | claude | f142-05's look test carried `@pytest.mark.usefixtures("fake_model")` twice | Fixed in round 2 |
| F7 | nit | claude | f142-04's tests show switching never notifies, not that a project's own work ending still does after a visit elsewhere (a fix dropping all done would pass) | Fixed in round 2: `test_all_done_still_notifies_after_a_look_at_another_project` |

### Round 2 (2026-10-28)
- **f142-04** keeps `done` as a map by project inside the one `notify:seen` key. "All work done" needs that project's own last look to have been "not done"; a project never seen, or the old plain `true`/`false`, counts as nothing to compare, so the first look after the upgrade stays quiet. The map survives a stale key (it's written before the 60-second check). Its edited test (`test_compare_uses_one_key_not_per_project`, renamed `…_per_project_done`) keeps its asserts and now fails on the old code, since the idle project's page has `data-all-done="true"`; the new old-shape test fails on it too. Right.
- **f142-05** adds `notify.planner_message`: a reply that worked says "The lead answered you", a look "The lead looked at a blocked ticket", a failed job "The lead couldn't answer you", each opening the card's thread. A look that fails also says "couldn't answer you"; the thread shows the failure there, so I left it. Its three tests cover the ticket's Done when: the block then the look, in order, with their links; the failure; no second "decision" for a ticket blocked again while open. The first two fail on the old code.
- Checks, with the review's changes: `tests/runner` 1706 passed, `tests/factory_dashboard` 1029 passed; ruff clean.

Checkpoint verdicts: C1342-1 (own-project ids lack the prefix) **confirmed**, fixed by `f142-02-fix-own-project-ids-notify-twice`. C1347-1 (no test flips done on a second project) **confirmed**, a nit, filled as F7. F1 and F2 were **missed**: both in f142-01's diff, which the checkpoint read. f142-05's checkpoint never ran (parked for Claude's limit), so nothing there counts as missed.

Score: 8/10 (round 1: 7). The ntfy sender is careful (never raises, no item text leaves the machine, nothing stored, tests never reach the network) and the doc is clear. Both fixes are small and right first time; the dashboard half needed one checkpoint fix and two review fixes in all.

Checked and fine: no card title, reply or item text in any ntfy body or header; a failed or slow post is one report note and the job goes on; the network call runs on an autocommit connection, so it holds no database lock; an item stored again while open sends nothing; `doctor` reads the setting without sending. Security: the topic is the only lock, as ADR 31 accepted; the notification carries the project's name and a kind only, and its link is the home address. With the review's fixes, ruff and mypy are green; `tests/runner` and `tests/factory_dashboard` together ran to 91% with no failure before the 10-minute limit of one call stopped them; in two more runs, the files this milestone touched (`test_overview.py`, `test_app.py`, `test_notify.py`, `test_setup.py`, `test_owner.py`: 305 tests) and the rest of `tests/factory_dashboard` (687 tests) pass in full.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing added: every finding is fixed or in a ticket.

## Factory
- Flow: two lead tickets and two developer tickets, all first attempt; one checkpoint, one fix ticket; no stops, no limit waits, no parks, no interventions by you after the plan.
- Models: Opus built the two runner tickets ($4.12) and planned ($22.82, five jobs; the ADR made it the bigger share); Sonnet's checkpoint $0.24; the local model 9.9M tokens in for the dashboard half.
- What worked: splitting by risk. The request that leaves the machine went to the lead, the dashboard words to the local model, which followed F114's worked examples closely.
- Round 2: f142-04 by the local model, first attempt, 37 minutes, checkpoint $0.17; f142-05 by the lead on Sonnet, $0.79 over two jobs, after five parks for Claude's limits and one interrupted run over four days. No stops for you.
- What didn't (round 2): my round-1 routing. F3's fix was ten lines in protected `runner/`; lead.md says the review fixes that itself, and I wrote a "local" ticket instead, which cost four days of waiting. Nothing new to add: the rule exists; I apply it.
- What didn't: the checkpoint judged the ids and missed the words and the "all done" flag in the same diff. What to change: a ticket whose Done when names a wording ("titled 'B: ' then its usual title") should name a kind whose usual title carries data (a reply on a titled card), so the developer's test can fail; I'll write them that way. No new check: it's ticket craft, added to ADR 02's log.

<!-- runner report -->
<!-- /runner report -->
