# Review: F142, phone notifications from every project, and with the dashboard closed

- **Status:** review round 1 done; two fix tickets in the line (f142-04, f142-05), then sign-off.

## Sign-off sheet

### 1. What changed
You get notifications again, and from every project. Two things changed:
- **With the dashboard open, on any project:** a page open on Travel-companion now notifies for Softfield too (and the other way round). A notice from another project starts with its name, for example "softfield: The lead replied: <the card's title>", and a tap opens that card on its own project. Moving between projects doesn't notify the same thing twice.
- **With the dashboard closed:** the runner sends each thing that needs you to the free **ntfy** app on your phone, the moment it stores it, screen off and browser closed. It says only the project and the kind of thing ("softfield · The lead answered you", "softfield · A card is ready for your sign-off", "softfield · A review stopped", "softfield · A ticket needs your decision", "softfield · Claude's reserve: your choice"), never a card's title or a reply's words. Several things on one card at once are one notification. A tap opens the page where you act, on the home Wi-Fi.
- Nothing is sent until you set it up (below). `softfield doctor` says whether you have.

### 2. How to test it yourself
1. Set the phone up once, following [`docs/notifications-on-the-phone.md`](../../docs/notifications-on-the-phone.md): on the machine run `softfield notify setup`, subscribe to the topic it prints in the ntfy app, then run `softfield notify test`. "softfield · Notifications work" arrives within seconds.
2. In Chrome on the phone, turn off the dashboard's own notifications (the doc's "Nothing twice"), so each thing comes once.
3. Close the dashboard and lock the phone. From the computer, send a message on any Softfield card.
4. When the lead replies, the phone shows "softfield · The lead answered you". On the home Wi-Fi, a tap opens that card's conversation.
5. On the computer, with notifications allowed in its browser: open the dashboard on Travel-companion's Overview and leave it in front. Send a message on a Softfield card. When the lead replies, a notification titled "softfield: The lead replied: <the card's title>" comes, and a click opens the Softfield card's conversation.
6. Click between Travel-companion and Softfield a few times: nothing notifies again. (Until f142-04 merges, switching from a busy project to an idle one can say "All work done"; see Left for later.)

### 3. Left for later
- **f142-04** (in the line): switching between a busy project's page and an idle one's says "All work done" each time. The fix keeps "all done" per project.
- **f142-05** (in the line): when a ticket is blocked, the phone gets "A ticket needs your decision" and then, after the lead's look, "The lead answered you", though you wrote nothing; a failed reply says the same. The fix words them "The lead looked at a blocked ticket" and "The lead couldn't answer you".
- Several notices bundled from different projects open the Planning room of the page's own project. Rare (two new things in one 5-second look); left as is.

### 4. Decisions waiting for you
None. ADR 31 (accepted, amended at your word on 2026-10-19) is now code.

### 5. How the work went
- 2026-10-16 to 10-19: planned in the Planning room over five planner jobs ($22.82), including ADR 31 and its amendment (nothing stored twice).
- 2026-10-23 02:09 ([session](../sessions/2026-10-23-0209.md)): `f142-02-ntfy-sender`, the lead's ticket (protected `runner/`), first attempt, 14 minutes, $3.22.
- 2026-10-23 02:28 ([session](../sessions/2026-10-23-0228.md)): `f142-03-phone-steps`, the lead's, first attempt, 5 minutes, $0.90.
- 2026-10-23 10:00 ([session](../sessions/2026-10-23-1000.md)): `f142-01-notify-every-project` by the local model, first attempt, 77 minutes; a checkpoint ($0.24) found the ids differed between a project's own page and the others'; fix ticket `f142-02-fix-own-project-ids-notify-twice`, local model, first attempt, 62 minutes. 9.9M local tokens for the two.
- Lessons:
  - The checkpoint caught the id slip but not two others in the same diff: other projects' notices were worded without their cards' titles, and one "all done" flag was shared by every project. Its tests used an `adr` item, whose words don't depend on titles, so they couldn't see it. A worded notice is tested with a kind whose words come from the data.
  - Two of the developer's tests passed with nothing to check (an `if`-guarded assert, a "/ in the key" check any id passes). The review tightened them.
  - The lead's two tickets on the runner went in first time and needed only one small fix (F4).

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** once f142-04 and f142-05 merge, a week of ntfy will show whether the phone gets too much. If it does, the next step is quiet hours or a daily digest for the less urgent kinds (the reserve switch), which ADR 31 left out. I'd plant it only if you find yourself muting the app.

### 7. What clogged the factory line
- **Planning to building, 3½ days** (plan settled 2026-10-19 23:20, first ticket 2026-10-23 02:09). The plan needed ADR 31's amendment, then the card waited its turn behind cards above it on the board; the factory merged other cards' tickets meanwhile. Nothing to unclog: the board's order working.
- **f142-01 waited on F114's fix tickets** (f114-07 to f114-10, which changed the same `notify.js` and tests), by design, to avoid two branches on the same lines. F114's chain of six test fixes over six days (see its review) is what held it.
- **The local model's two tickets took 2 h 19 min** for about 30 lines of code; first attempts, no limit waits, no stops for you. The ids slip cost one extra hour (the fix ticket); a ticket listing the exact ids (`softfield/owner-129`, own project included) in Done when would have avoided it. It did say so in Context; the developer read "own project keeps its titles" as "keeps its ids".

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
| F2 | should-fix | local | One "all done" flag for every project: switching from a busy project's page to an idle one's says "All work done" | Ticket `f142-04-fix-all-done-per-project` |
| F3 | should-fix | local | A look at a blocked ticket and a failed reply both notify "The lead answered you"; the block's notification is untested | Ticket `f142-05-fix-a-look-is-not-an-answer` |
| F4 | nit | claude | `notify setup` on a `[notify]` with an empty `ntfy = ""` added a second key, leaving the machine's whole settings file unreadable | Fixed, with a test |
| F5 | nit | claude | `test_data_notices_ids_start_with_project_name` accepted any prefix; `test_data_notices_excludes_forgotten_project` passed with no notice | Fixed: exact ids, the own item present |

Checkpoint verdicts: C1342-1 (own-project ids lack the prefix) **confirmed**, fixed by `f142-02-fix-own-project-ids-notify-twice`. F1 and F2 were **missed**: both in f142-01's diff, which the checkpoint read.

Score: 7/10. The ntfy sender is careful (never raises, no item text leaves the machine, nothing stored, tests never reach the network) and the doc is clear. The dashboard half needed a checkpoint fix and leaves two should-fix items for the line.

Checked and fine: no card title, reply or item text in any ntfy body or header; a failed or slow post is one report note and the job goes on; the network call runs on an autocommit connection, so it holds no database lock; an item stored again while open sends nothing; `doctor` reads the setting without sending. Security: the topic is the only lock, as ADR 31 accepted; the notification carries the project's name and a kind only, and its link is the home address. With the review's fixes, ruff and mypy are green; `tests/runner` and `tests/factory_dashboard` together ran to 91% with no failure before the 10-minute limit of one call stopped them; in two more runs, the files this milestone touched (`test_overview.py`, `test_app.py`, `test_notify.py`, `test_setup.py`, `test_owner.py`: 305 tests) and the rest of `tests/factory_dashboard` (687 tests) pass in full.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing added: every finding is fixed or in a ticket.

## Factory
- Flow: two lead tickets and two developer tickets, all first attempt; one checkpoint, one fix ticket; no stops, no limit waits, no parks, no interventions by you after the plan.
- Models: Opus built the two runner tickets ($4.12) and planned ($22.82, five jobs; the ADR made it the bigger share); Sonnet's checkpoint $0.24; the local model 9.9M tokens in for the dashboard half.
- What worked: splitting by risk. The request that leaves the machine went to the lead, the dashboard words to the local model, which followed F114's worked examples closely.
- What didn't: the checkpoint judged the ids and missed the words and the "all done" flag in the same diff. What to change: a ticket whose Done when names a wording ("titled 'B: ' then its usual title") should name a kind whose usual title carries data (a reply on a titled card), so the developer's test can fail; I'll write them that way. No new check: it's ticket craft, added to ADR 02's log.

<!-- runner report -->
<!-- /runner report -->
