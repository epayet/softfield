# Review: F31, proposals close the loop

- **Status:** reviewed on 2026-10-12, round 1; waits for the owner's sign-off. One ticket, f31-04 ("What to do now"), is still in `tasks/later/`: it waits for a mock-up you haven't seen yet.

## Sign-off sheet

**Expected:** approving or rejecting a proposal is one press that shows at once, the thread leaves your desk when everything in it is settled, a note is never refused unseen, and planting is one box.
**Done when:** Approve from a phone: the button goes, the dock says it's on its way, then "approved · queued …", and the thread shows under Archived as approved. Reject a seed card's plan: nothing queued, the branch and the card gone, the thread archived as rejected. A new reply shows information as lines and actions as coloured boxes, with "What to do now" under it (**not built yet**: f31-04). Plant a 300-character note: planted, and the lead's reply names the card.

### 1. What changed
- **Approve can't be pressed twice.** On a proposal's page, pressing Approve plan, Accept ADR, Plant it or Send back swaps the buttons at once for a dashed orange box, "On its way · the runner applies it at its next pick". A reload shows the same box. Once the runner has done it, the page says "Approved" with the runner's own words, and has no buttons.
- **Reject (won't do).** Each open proposal has "Reject…", which says what it takes with it before you confirm. Rejecting a plan, ADR or mock-up removes the card's plan branch with every draft on it; a card with nothing built is removed too. Rejecting a merge or a seed closes only that proposal.
- **A settled thread leaves your desk.** When every proposal of the lead's latest reply is approved or rejected, the runner adds one line to the thread ("Approved by the owner on …: queued …", or "Rejected by the owner on …: won't do") and archives it. Under Archived it reads "approved" or "rejected". Writing on the thread opens it again.
- **Each proposal says where it stands,** in the same words on its page and on the thread: open, on its way, approved, rejected, sent back, or replaced by a newer reply.
- **"What approving changes" says who builds each ticket** (lead or developer) and its difficulty, and colours added, changed, set aside and removed.
- **Didn't go through.** A note, message or send-back the runner refused now waits first on the desk, counted, with your words, the reason, Try again and Dismiss.
- **Plant is one box.** You type the note; nothing is refused for its length. The card's heading is its first words until the lead's first reply names it (a commit "F32 named by the lead").
- **The lead's replies:** two lines of prose at most, cards named with their title, and one point for a bare "agreed". Each point now carries what it leads to (information, a ticket, an ADR…), stored but **not drawn yet**.
- *(Fixed in this review)* A merge you rejected was still applied when you approved the thread's plan. It is now left alone.
- *(Fixed in this review)* The lead was told to list only the proposals it changed. A proposal it left out then read "replaced" (or stayed "sent back") with no buttons, and the thread could close with the plan never approved. The lead now lists again everything that still waits for you.

### 2. How to test it yourself
Restart the runner first (`uv run runner run`): this review changed its code.
1. On your phone, open `/planning`. Type a long note (300 characters) in the one box and press **Plant and ask the lead**. It shows under Coming at once. After the runner's pick and the lead's reply, the card has a short title the lead gave it.
2. Open a proposal waiting on your desk and press **Approve plan**. The buttons go at once and the dashed orange box appears. Reload: still the box, no button.
3. After the runner's next pick, reload: the page says "Approved" and "The runner said: approved plan/…: queued …". On `/planning`, the thread is gone from your desk and listed under Archived as "approved".
4. On a seed card's plan you don't want, tap **Reject…**, read what it takes, then **Reject**. After the pick: the card is off the board, nothing was queued, and its thread is under Archived as "rejected".
5. If a note is ever refused, it shows first on the desk under "Didn't go through". **Try again** puts your words back in the box without sending them; **Dismiss** takes the item off at once.

### 3. Left for later
- **f31-04, "What to do now"** (`tasks/later/`): the open proposals right under the lead's latest reply with their buttons, information points as plain lines, action points as coloured boxes, and tappable card numbers. It waits for a mock-up, which I owe you.
- In `docs/backlog.md`, all nits:
  - f31-F5: a sent-back proposal stays "sent back" until the lead lists it again. The lead is now told to; the page could also open it again by itself once the lead has replied.
  - f31-F6: a reject posted with a card's full key (not what the dashboard sends) would remove the branch but leave the proposal showing open.
  - f31-F7: a seed you rejected can still be planted from a page left open before the reject.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-08 03:35, runner: f31-06 (refused notes on the desk) merged first time as a headless lead ticket, 35 min, about 1.1M Claude token-equivalents, no local tokens ([session](../sessions/2026-10-08-0335.md)).
- 2026-10-08, terminal session with the owner: the lead built f31-05, the settling half of f31-01 (with F55), then f31-01's Reject and f31-02. No runner session, so no report.
- 2026-10-10: f31-03 waited for Claude's weekly reserve (1% left) through two runs ([08:54](../sessions/2026-10-10-0854.md), [19:10](../sessions/2026-10-10-1910.md)), then was blocked: its work was done, but a file the F12 review left on main failed the layout check.
- 2026-10-12, terminal session: f31-03 landed from its branch once main was green again ([narrative](../sessions/2026-10-12-lead.md)).
- Lessons:
  - **A new button has to be checked against every older path that does the same thing.** Reject was right on its own, but Approve plan read the thread's merges without asking whether one was rejected.
  - **A rule in the code needs its line in the prompt.** F31 made "the latest list" decide which proposals keep their buttons and when a thread closes; the lead's prompt still said to list only what changed.
  - **Four of five tickets were built in a terminal with no checkpoint,** as with F41, F50 and F55. The review was the only reader, and found one real gap each time.
  - f31-02 was a developer ticket (difficulty 5) the lead built itself: nothing learned about developers.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - The mock-up for f31-04, on a real thread of yours, so the last third of this card (the part you'd see most) can be queued. Ask for it on F31's thread, or I draft it at the next planning job.
  - F51 (ready) changes the same Approve button and `_approve_plan`; it should build on this review's fix.
  - A Sonnet checkpoint on each terminal commit of the lead's (about $0.25), suggested in F50's review, would likely have caught f31-F1: the Done when says "only that proposal settled".
  - F106 D5 (a red main blocks nothing) is the fix for what held f31-03 for two days.

### 7. What clogged the factory line
I couldn't read the metrics database from this job (no query command is allowed here), so these come from the session reports, without hours. Fix for that: allow `uv run runner report` in a review job's commands, so the lead can read the numbers it must quote.
- **f31-03 waited for Claude's weekly reserve** (10 Oct, two runs). What unclogs it: the reserve switch, which the session report already asked for.
- **f31-03, done but blocked by a red main** (10 to 12 Oct): a scratch test file from the F12 review failed the layout check for every ticket. What unclogs it: F106 D5, and the lead.md rule that a ticket repairing main gets priority 0.
- **f31-03 timed out once waiting on a background `check-all`** it couldn't watch. Fixed on 12 Oct: the shell note now says checks run in the foreground. This review hit the same wall from the other side: the tests take over 10 minutes, the limit of one foreground command. F71's study (f71-02) is where that gets answered.
- **f31-04 waits for a mock-up** nobody was asked for. What unclogs it: the planner drafting a mock-up as soon as a UI ticket is set aside for one (F72, ready, makes mock-ups the default).

## What was built
- **f31-06, D9** (`runner/requests.py` `owners_words`, `refused`, `_dismiss`; `factory_dashboard/planning.py` `_refused`; `owner_requests.dismissed`): the desk's first group, read leniently so a value the runner couldn't parse still shows whole.
- **f31-05, D7** (`runner/planner.py` `heading`, `_note_text`, `planting`; the `#plant` form): `{"text", "area"}`, the older `{"title", "thoughts"}` still planted.
- **f31-01, D1–D3** (`runner/planner.py` `proposal_state`, `proposal_requests`; `runner/requests.py` `_settles`, `_settled`, `_close_if_settled`, `_latest`, `_reject`): one state function for the runner, the desk, the thread and the review page.
- **f31-02, D3 and D8** (`factory_dashboard/planning.py` `_standing`, `_who`; `proposal.html`'s dock).
- **f31-03, D4, D6, D7's title** (`runner/planner.py` `_outcomes`, `_title`, `named_card`; `runner/loop.py` `_name_card`; `runner/prompts.py`): a title that would set the card's state, area or `After:` is ignored with a note, and a failed naming commit never stops the run.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f31-F1 | should-fix | claude | `_approve_plan` applied every `merge` of the thread's latest reply not yet applied, a rejected one too: after "won't do" on a merge, Approve plan removed the duplicate's card anyway (or, when the duplicate had tickets, refused the whole plan for a merge the owner had rejected) | Fixed: `_rejected` in `runner/requests.py`, read by `_approve_plan`; `test_approving_a_plan_leaves_a_rejected_merge_alone`, `test_approving_a_plan_still_applies_the_merges_not_rejected` |
| f31-F2 | should-fix | claude | D1 and D3 hang on "the latest list", but the planner prompt said "list every proposal you drafted or changed this turn". A partial list left the others "replaced" with no buttons and let the thread close as approved with the plan unapproved; a send-back answered with no list left the proposal "sent back" for good | Fixed in `runner/prompts.py` (both planner prompts): a new list replaces the last, so list again what still waits, and a sent-back proposal kept as it is; `test_both_planner_prompts_say_a_new_list_of_proposals_replaces_the_last` |
| f31-F3 | nit | claude | A thread closed by a reject after an approval said "Approved by the owner on …: rejected seed-1" | Fixed: "Settled by the owner on …" when the closing act is a reject; asserted in `test_one_proposal_approved_and_one_rejected_closes_as_approved` |
| f31-F4 | nit | claude | f31-02's Done when names "sent back, with no buttons and no Comment…"; no test showed it | Added `test_a_sent_back_proposal_says_so_with_no_buttons` |
| f31-F5 | nit | backlog | The code's own backstop for f31-F2: `proposal_state` knows only requests, not that the lead has answered a send-back | `docs/backlog.md` |
| f31-F6 | nit | backlog | `_reject` reads its thread through `thread_key`, `_settles` and `proposal_state` compare the subject as posted | `docs/backlog.md` |
| f31-F7 | nit | backlog | `_seed` doesn't read a seed's state: a rejected one can be planted from a stale page | `docs/backlog.md` |

Tests read: the reject and settle tests in `tests/runner/test_requests.py`, `proposal_state`'s table in `tests/runner/test_planner.py`, f31-03's loop and prompt tests, and f31-02's page tests. They cover each Done when but the two above. The one existing test this review changed, `test_one_proposal_approved_and_one_rejected_closes_as_approved`, gained an assertion and lost none.

No checkpoint ran on this card, so there is nothing to judge. French: nothing to check, the dashboard is English only and no `coucou/locale/` file changed. Checks after the fixes: `uv run pytest -q tests/unit tests/integration tests/runner tests/factory_dashboard` passed; ruff, format and mypy are clean.

Score: 7/10. One state function shared by four readers, careful refusals, and tests that fail without the change. It loses points for the rejected merge Approve still applied, and for changing what "the latest list" means without telling the lead that writes it. A third of the outcome (f31-04) isn't built.

## Factory
- **Flow:** five tickets. One merged by the runner first time (f31-06). Three built by the lead in a terminal with the owner. One (f31-03) done by a headless job, then held two days by the reserve and a red main, and landed by hand. No escalation, direction or checkpoint. The owner moved f31-01's priority twice on 2026-10-08.
- **Models:** Opus only. No developer work: four tickets are protected runner code, and f31-02, the one developer ticket, was built by the lead.
- **What to change:** see "What next" and "What clogged the factory line". Nothing here needs an ADR.

## Workflow observations
- The start tag `f31-when-i-click-on-approve-plan-start` dates from 2026-10-07, so the milestone diff holds 309 files of every card built since. The review read F31's six commits instead. A card built in pieces across days would be better served by a diff of its tickets' commits (the `Task:` trailer, or the tickets' `files:`).
- A review job can't finish its required test run in one foreground command: the four suites took more than the 10-minute limit and the run was moved to the background.

<!-- runner report -->
<!-- /runner report -->
