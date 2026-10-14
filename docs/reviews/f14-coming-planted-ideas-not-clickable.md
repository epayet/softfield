# Review: F14, a waiting plant or message can be edited or cancelled

- **Status:** reviewed on 2026-10-14, round 2 of 3: the review loop has stopped with nothing open. The fix ticket (`f14-04-failed-edit-shows-on-desk`) is merged; all of it is ready for you to try and sign off.

## Sign-off sheet

**Expected:** your note was "they look like I can click on them to edit or cancel them but I can't", then "i want to be able to edit or cancel something in the queue that hasn't been sent yet". A plant or a message still in Coming can be tapped, edited or cancelled; the change shows at once, on its way, and the runner applies it first at its next pick. A change that arrives too late says so plainly.
**Done when:** a waiting plant on the desk opens with its words, Save and Cancel it; a waiting message on a thread has Edit and Cancel it; after either, the row shows what was asked at once with the dashed orange edge and can't be changed again; a cancelled plant makes no card and no reply from the lead, an edited one is planted with the new words; a change that comes too late finishes as "too late: already planted" (or "already sent") and the dashboard shows it.

### 1. What changed
- On the Planning desk, a plant waiting in Coming opens when you tap it, in place: its words in a box, **Save** and **Cancel it**. A note written in one box opens as one box; an older plant opens as its title and thoughts.
- On a thread, a message you sent that the runner hasn't taken yet has **Edit** and **Cancel it** under it. Edit opens its text in place with Save; your comments on the lead's points go along unchanged.
- After Save, the row shows the new words at once, "changed", with the dashed orange edge. After Cancel it, it is struck through, "cancelling at the runner's next pick". Either way the buttons go until the runner has taken it.
- With every waiting message on a thread cancelled, the Send box comes back, and the thread leaves Coming on the desk (this last part fixed in this review).
- The Now page's "Next in line" shows the same for a plant: the new title, or struck through.
- At its next pick the runner applies changes before anything else: a cancelled plant makes no card and no commit, a cancelled message never reaches the lead, an edited one goes with the new words.
- A seed the lead proposed and you approved can be cancelled while it waits, not edited: its words are the lead's.
- An edit that didn't go through (it came too late, or the runner couldn't take its words) now waits on the desk under **Didn't go through**: "Your edit of Rubber ducks" or "Your edit on The planning room", your new words in full, what the runner said, and Dismiss. A message's edit also has **Try again**, which opens its thread with the words in the reply box; a plant's has Dismiss only, since the idea is a card by then and planting the words again would make a second one. A cancel that came too late shows nothing there: it carried no words (added in round 2, `f14-04`).

### 2. How to test it yourself
1. On your phone, open Planning and plant a note with **Plant** (not "Plant and ask the lead").
2. Tap its row in Coming straight away: it opens with your note, Save and Cancel it.
3. Change a word and press Save: the row shows the new words, "changed · planting at the runner's next pick", dashed orange, and no longer opens.
4. Plant a second note, open it and press Cancel it: it is struck through, "cancelling at the runner's next pick".
5. Open the Now page: "Next in line" shows the first plant with its new title and the second struck through.
6. Open a card's thread and send a message. Under it, press Edit, change it, Save: the new text shows at once, "changed".
7. On another thread, send a message and press Cancel it: it is struck through and the Send box is back. On the desk, that thread is no longer in Coming.
8. After the runner's next pick (up to an hour while a job runs): the edited note is a card with the new words, the cancelled one made none, the edited message is on its thread with the lead's reply on its way, the cancelled one is gone.
9. The "too late" case, which needs a page older than the runner's last pick: open Planning in two tabs and plant a note. Once the runner has planted it (the first tab, reloaded, shows the card), go to the second tab without reloading, open the note's row there, change it and Save. After the next pick, the desk shows it under Didn't go through, "Your edit of …", with your new words and "too late: already planted". Press Dismiss: it leaves.

I didn't look at it on a screen myself: a review job has no browser to look through. Eight tests open these pages in Chromium, two of them at a phone's width, press the buttons and read what shows without a reload.

### 3. Left for later
- Nothing of F14's own is left: `f14-04-failed-edit-shows-on-desk` merged in round 2.
- Backlog: after Send on a thread, the page probably holds the conversation twice nested (invisible, an older line of script); to check and fix when that script next changes.
- Backlog: a message's edit that the runner refused for its words, while the message still waits, has a Try again that opens a thread with no reply box yet (the lead's answer is awaited). The words stay on the desk and the message's own Edit is back, so nothing is lost; rare, and a two-line fix when that code next changes.
- Not in F14 by decision (D3, D4): a message the runner has taken can't be edited, and a queued reply from the lead can't be stopped. A planted card can still be removed with "Remove seed".

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-07: planted by you; planned as three tickets, one the lead's (the runner is protected), two for a developer.
- 2026-10-13, 16:20 session: f14-01 (the `change` request in the runner) built by the lead and merged at its first attempt, 24 minutes. [Session](../sessions/2026-10-13-1620.md).
- 2026-10-13, evening: f14-02 (the desk's editor) went to the developer. Three attempts, each stopped after 10 minutes of reading with no edit, one direction in between; escalated, and the lead built it in 42 minutes. No session report for that run is in `docs/sessions/`.
- 2026-10-14, 00:55 session: f14-03 (the thread's buttons) went to the developer. Two attempts stopped with no edit, a direction, then a 77-minute attempt that built it with five faults and stopped on an existing test the ticket hadn't named; escalated, and the lead finished it in 32 minutes. 11.3 million local tokens. [Session](../sessions/2026-10-14-0055.md).
- 2026-10-14: this review, round 1. One small fix, one test, one lead ticket, one backlog line.
- 2026-10-14, 03:20 session: f14-04 (the failed edit on the desk) built by the lead and merged at its first attempt; no local tokens. [Session](../sessions/2026-10-14-0320.md).
- 2026-10-14: this review, round 2. The fix read against its ticket line by line: resolved, one nit to the backlog, nothing to fix.
- Lessons:
  - **Both developer tickets came back to the lead,** as F13's and f9-25's did: four tickets in a row on the planning pages, none merged by a developer. Each needed the 1,000-line `planning.py`, a template with its script, and the 2,700-line `test_planning.py`; the developer reads for ten minutes and is stopped before its first edit. A direction didn't help either time. Written into "Known range": a ticket that redraws part of a planning page after a post is the lead's from the start, until that test file is split.
  - **The plan's last "Done when" line reached no ticket for messages.** "The dashboard shows that result" was written into f14-02 for plants and left out of f14-03. The review found it by reading the milestone's lines against the tickets', one by one; that check belongs at planning, before the tickets are queued.
  - **The lead's own ticket was the best of the three:** f14-01 has 47 test cases for about 80 lines, every refusal and the order of two changes included, and nothing to fix.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Split `tests/factory_dashboard/test_planning.py` by page (the desk, a thread, proposals), with its helpers in a `conftest`. It is the file every planning ticket has to read, and the likeliest reason four developer tickets in a row made no edit. Text ready to plant if you agree: "Split the planning tests by page: the desk, a thread, proposals. A developer reads 2,700 lines of tests before its first edit and is stopped at 10 minutes; four tickets in a row came back to the lead. Open question: does the same hold for test_line.py and test_overview.py?"
  - F93's change (the no-edit stop at 20 minutes, `f93-01`, ready) would have given both tickets' first attempts a chance; run it before the next planning-page ticket.
  - F19 (the planning page live) will make the "too late" case rarer: it happens when a page is older than the runner's last pick.
  - bug-01 again: this review was handed 70 files and 2,577 lines; F14's own are about 1,100.

### 7. What clogged the factory line
- **Six days from your note to the first merge** (2026-10-07 to 2026-10-13), waiting its turn and behind a red main, as F22 did. What unclogs it: the same as F22's review said (small tickets first; developer tickets wait while main is red).
- **About two and a half hours of developer time that merged nothing:** six attempts on two tickets, five stopped at 10 minutes with no edit and one of 77 minutes that timed out (from the jobs table). What unclogs it: such tickets go to the lead from the start ("Known range"), `f93-01`, and the split of the test file above.
- **Two directions that changed nothing** ($0.87 and $0.73): both followed two no-edit attempts, and "Known range" already says to skip the direction then (f9-25). What unclogs it: the runner could escalate straight after two no-edit stops instead of asking for a direction. Text ready to plant: "After two attempts stopped with no edit, skip the direction and escalate: a direction has not once helped there (f9-25, f13-01, f14-02, f14-03). Open question: one more try at 20 minutes first, once F93 is in?"
- **Two hours between f14-02's last attempt and its escalation** (18:24 to 20:22 in the jobs table): the escalation waited for its turn or for Claude; I couldn't tell which from here.
- **The review:** four minutes for the three test folders, three and a half for the planning tests, and 2,577 lines to sort. What unclogs it: bug-01, and F71's slow-tests study (`f71-02`, ready).

## What was built
- **The runner** (`runner/requests.py`, `runner/metrics.py`; f14-01, the lead): a request kind `change` whose subject is the id of the waiting request it changes. `apply_requests` applies every open change first, then reads the other requests again, so a cancelled plant or message is never applied and an edited one goes with its new words in the same pick. A cancel finishes its target as "cancelled by you", which `refused` doesn't count as a refusal. An edit replaces the target's words and keeps what else it said (its area, "ask the lead"); the new value is read as the pick will read it before it is stored, so a bad edit changes nothing. Too late once the target is done. A change commits nothing, so it never waits for main. `factory_dashboard/requests.py` accepts the kind.
- **The desk** (`factory_dashboard/planning.py`, `templates/planning.html`, `overview.py`, `_partials/queue.html`; f14-02, built by the lead in escalation): `open_changes` reads the open changes by target; `coming` gives each waiting plant a row that opens (a `<details>` with the editor) or, with a change on its way, a dashed row with the change and its polling status. A change on a plant the runner has already taken keeps a row until the runner answers it. After a post, only Coming is drawn again. The Now page's plant rows show the same.
- **The thread** (`factory_dashboard/planning.py`, `templates/thread.html`; f14-03, finished by the lead in escalation): a waiting message carries its request's id and its open change; the template adds Edit, Save and Cancel it, and one listener that draws the conversation again after a post. A cancelled message no longer counts as waiting for a reply.
- **The failed edit on the desk** (`runner/requests.py`, `factory_dashboard/planning.py`, `templates/planning.html`; f14-04, the lead, round 2): `owners_words` reads a `change` that is an edit (a cancel carries none), `refused` counts one whose result isn't "changed", and `_dismiss` takes it as it takes the other three kinds. On the desk, `_refused` lists it with a title that names what was edited (`_failed_edit` looks the target up in its own project only), and `_again` gives a message's edit to its own thread's reply box. A retry sent from there names the change, so the row leaves the desk once (F48 D2).
- **Tests:** 47 cases in `tests/runner/test_requests.py`, 2 in `tests/factory_dashboard/test_overview.py`, 18 in `tests/factory_dashboard/test_planning.py` (7 in Chromium, one added by this review), 2 rows in `tests/factory_dashboard/test_requests.py`. Round 2 added 5 tests (32 cases) at the runner and 8 on the page (14 cases, one in Chromium).

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | ticket (lead) | An edit that didn't go through shows nowhere once the pick has passed, and a message's never shows: after Save on a message the runner had taken, the thread is drawn again with the message stored and no status. The milestone's last "Done when" line ("the dashboard shows that result") holds for plants only while the page stays open, and the owner's new words stay in `owner_requests` alone: against "the owner's words are never refused unseen" (2026-10-08) | **Resolved in round 2** by `f14-04-failed-edit-shows-on-desk` (the lead's, merged as `fcaa205` at its first attempt): such an edit joins "Didn't go through" on the desk, with its words and the reason, until dismissed. Every "Done when" line of the ticket has a test |
| F2 | should-fix | claude | The desk's Coming kept listing a thread as "waiting for the lead" after its only waiting message was cancelled, while the thread itself showed the Send box again: the two pages disagreed until the pick | Fixed in the review: `coming` (`factory_dashboard/planning.py`) leaves out a `plan_message` with an open cancel; `test_a_cancelled_message_no_longer_puts_its_thread_in_coming` holds it (an edited message still shows, a second one brings the thread back) |
| F3 | nit | backlog | The reply form's older listener in `thread.html` re-fetches with `select: "#conversation"` and `swap: "innerHTML"`, which puts a `#conversation` inside `#conversation` after each Send. Invisible; F14's own listener uses `outerHTML` and its test counts one | `docs/backlog.md` |
| F4 | nit | backlog | Round 2, in f14-04: a message's edit refused for its words (not too late) gets a Try again to its thread's `#reply`, but the message it names still waits, and the thread draws "Next for the lead" instead of the reply box. Nothing is lost: the words stay on the desk and the message's Edit is back. Rare: the editor would have to send words the runner can't read | `docs/backlog.md`: give `again` only when the message is done |

Round 2, read in f14-04 and found sound, no finding:
- **A cancel never shows,** whatever its result: `{"cancel": true}` carries no words, so `refused` and `_dismiss` leave it alone, and a test holds each of the four results. A value that mixes a cancel with words (the runner refuses it) shows its words.
- **Nothing crosses projects.** A change that names another project's request, another kind, or no request shows as "Your edit" with the owner's own words and Dismiss; a test plants a message in a second project and checks none of it reaches the page or a reply box.
- **The three older kinds read as before.** `owners_words` and `refused` kept every earlier assertion; no existing test was edited, the diff only adds.
- **The words are escaped.** The message test saves `<bright>` and reads it back as text from the desk and from the reply box.
- **Too late is decided before the value is read** (`_change`), so a too-late edit always keeps its words for the desk, well formed or not.

Read and found sound, no finding:
- **Changes go first, and nothing races.** The dashboard still only adds rows; the runner alone finishes or rewrites one, and `change_request` updates only an open row. Two changes on one target apply in order; the desk's `open_changes` reads them the same way (a cancel wins, then the latest edit), and a test holds each side.
- **Scope of a change.** It is refused for a request of another project, another kind, a missing id, or an id that isn't digits; the owner's words stay off the console line (`_what`).
- **The templates' values.** The plant's title and text go through Jinja's escaping into `value=` and the textarea; the message's comments go back through `tojson` inside a single-quoted attribute (it escapes `'`); a browser test saves a title and a comment with double quotes in them.
- **Edited existing test:** one, `test_try_again_fills_the_box_only_with_a_refused_message_of_ours`. It looked for a `<textarea name="text"` anywhere on the page, and the new editor adds one; it now looks inside `<form id="reply">` and also asserts that the form is absent exactly while a message waits. Nothing was loosened.

No checkpoint finding was handed to this review, so there is none to judge. Security: nothing found; the new kind writes only through the runner's checks. French: nothing to check, no user-facing string and no `coucou/locale/` file changed (the dashboard is English only). Screenshots: no browser to look through in this job.

After the fix, `uv run pytest -q tests/unit tests/integration tests/runner` passes; the three dashboard test files touched by F14 gave 295 passed; ruff and mypy are clean on the edited files.

Round 2: `uv run pytest -q tests/unit tests/integration tests/runner` gave 1954 passed, 1 skipped. The review changed no code this round.

Score: 8/10 (7 in round 1). Every "Done when" line of the milestone now holds, and what merged is careful and well tested, the runner's part especially. It stays short of more because the last line reached the feature only through a review finding, and because the lead ended up writing all four tickets.

Stop reason: none. Both should-fix findings are resolved and the two nits are in the backlog, so the loop stops here at round 2.

## Factory
- **The flow:** three tickets; one lead ticket merged first time; two developer tickets escalated after three attempts each and were built or finished by the lead. Two directions, two escalations, no park, no limit, no stop for the owner. No checkpoint ran on F14's merges. Round 2: the fix ticket, the lead's, merged at its first attempt; the run then stopped as it should, since the ticket changed `runner/`, and a fresh process took this round.
- **Models and cost** (from the jobs table): Qwen (qwen3.6-35b-a3b) 0/2, about 127 minutes of attempts. Claude Opus before this review: $1.73 for f14-01, $0.87 and $0.73 for the two directions, $2.96 and $2.60 for the two escalations, $8.89 in all. Planning these two as lead tickets would have cost about the two escalations' price and saved the directions and four hours of line.
- **What to change:**
  - A ticket that redraws part of a planning page after a post is the lead's from the start (in "Known range").
  - At planning, read each of the milestone's "Done when" lines against the tickets' and name the ticket that carries it (F1; in `docs/task-writing.md`).
  - Split `test_planning.py`, and skip the direction after two no-edit stops (sheet, items 6 and 7; both as text to plant, since they are new work for you to order).

## Workflow observations
- No session report exists for the run that tried f14-02 (2026-10-13 17:46) or for the one that escalated it (20:22); F22's review missed the same run's report. The jobs table has the figures. If a run that ends on "runner changed, needs a fresh process" or on a stop skips its report, that is a bug to fix: worth a look when bug-01 is done.
- Round 2: the fix ticket's "merged" commit says "1 attempt, 0 s in all", and the session report counts 0 local tokens "on 1 task(s)" for a ticket the lead built: a lead ticket's time isn't in the figure that line reads. Suggested fix: when the next runner ticket touches the merge message, take the time from the lead's job row; not worth a ticket alone.
- Round 2's prompt asked for `git diff fce81ba^..main`, which holds round 1's own commit (the review report, the backlog, ADR 02) beside the fix: 14 files, 5 of them the fix. Reading `git show` of the fix's commit was enough. Same cause as bug-01: the range starts one commit too early.
- The round-1 prompt gave 70 files; about a third are F14's. The rest are F22, F95's `look` command, F93 and F114's plans, a terminal session on the gates, and the roadmap's removal.

<!-- runner report -->
<!-- /runner report -->
