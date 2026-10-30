# Review: F73 set a proposal aside for now

- **Status:** review round 1 done, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- Every open proposal's page (plan, mock-up, replan, ADR, merge, seed) has a "Not now" panel under the buttons with **Set aside**. It takes the whole conversation off your desk, drafts kept. A message from you on the thread opens it again.
- A plan, mock-up or replan also has **Refresh against main**. It is Send back with the words already written ("Check this against main as it is now…"), so you type nothing.
- A plan, mock-up or replan drafted three days ago or more says so above those buttons: "Drafted N days ago: the code may have moved. Refresh it before approving."
- On `/planning`, a new closed list **Set aside · N** sits just above **Archived · N**. Each line says what waits in it and when: "1 ADR, 1 plan · set aside 2 h ago". A thread closed by an approval or a rejection, or one you archived with nothing open, stays under Archived. Neither list counts in the Planning tab or the desk.
- After you press Set aside, the page shows it on its way. If you open the page again before the runner's next pick, it now reads "Setting aside at the runner's next pick" and the buttons stay hidden (the review added this).

### 2. How to test it yourself
1. On the phone, open a plan waiting on your desk (from "Proposals to review").
2. Scroll below Approve: the "Not now" panel shows Refresh against main and Set aside, each a full thumb-sized button.
3. Press Set aside: the buttons go and the request shows as asked. Reload: "Setting aside at the runner's next pick".
4. After the runner's next pick, open `/planning`: the card is gone from "Proposals to review", and "Set aside · 1" (closed) lists it as "1 plan · set aside … ago". Archived doesn't list it.
5. Tap it and write a message on its thread: after the runner's pick it is back on your desk.
6. On another plan, press Refresh against main: the lead's next reply revises the drafts.

### 3. Left for later
- An ADR or a merge waiting three days doesn't say how old it is: the note only shows where Refresh exists (backlog, F4).
- A merge whose card has already left main can show under Set aside as "1 merge" (backlog, F3; not seen).
- D5, as planned: a card whose tickets are already queued can't be set aside this way. The board's order (F15) and F106's button cover it.

### 4. Decisions waiting for you
None.

### 5. How the work went
- [2026-10-29 04:34](../sessions/2026-10-29-0434.md): `f73-01-set-aside-list`. Qwen stopped three times with no edit (one direction, $0.55). The lead finished it in the escalation ($1.32).
- [2026-10-29 09:14](../sessions/2026-10-29-0914.md) and [14:35](../sessions/2026-10-29-1435.md): `f73-02-set-aside-button`. Qwen stopped twice with no edit. The direction waited 4 h 40 min, mostly for Claude's five-hour window. A third no-edit stop followed, and the lead finished it in the escalation ($2.16).
- Lessons:
  - Five no-edit escalations in two nights (f26-02, f15-06, f73-01, f73-02) look like a slow model, not tickets too big. bug-48 (ready, from F15's review) makes the runner skip the direction on such a night. It would have saved F73 $1.10 and about 6 hours.
  - The "on its way" rule has to hold after a reload too, not only right after the press. The thread page's Archive already did this; the new button copied the press but not the reload. The review fixed it.

### 6. What next
- **Product:** on hold, as you asked (2026-10-04).
- **Factory:**
  - Run bug-48 before the next batch of developer tickets at difficulty 4. Until it lands, give the lead any planning-desk ticket that touches `test_planning.py` (over 2,000 lines): Qwen has made no edit on four of them this week.
  - When a plan offers a button that posts a request, have the ticket name the reload case too ("open the page again before the runner's pick"). I've added that to this review's lessons. It goes into `docs/task-writing.md` if it shows up again.

### 7. What clogged the factory line
- **About 4 hours of Qwen with nothing merged:** six 20-minute attempts, each 2–5 steps, all stopped for no edit. Fix: bug-48, then the lead takes such tickets on a slow night.
- **4 h 40 min waiting on f73-02's direction** (09:55 → 14:35): Claude's five-hour window went from 75 % to full by 11:46 and reset at 12:50. The run then held until 14:35 with nothing else to do. Fix: the same bug-48. With no direction to wait for, the ticket would have gone straight to escalation, behind the same window but one Opus job instead of two.
- No stops for you, and no ticket waited on another while agents sat idle (f73-02 depended on f73-01, which merged at 07:47, before f73-02 started).

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/planning.py`: `_put_aside` reads, for each thread archived "by you", its latest lead message with proposals. It counts the proposals still open or on their way with `proposal_state`, as `_open_proposals` does. `archived` and the new `set_aside` share `_archived_threads`, so no thread is in both lists. The list is read, not stored (D1): nothing changed in the runner.
- `factory_dashboard/templates/planning.html`: `<details id="set-aside">` above `#archived`, built like it.
- `factory_dashboard/proposal.py` and `templates/proposal.html`: the "Not now" panel with `#set-aside-button` (the `archive` request), `#refresh-button` (`send_back` with `REFRESH_WORDS`), `#stale` from `drafted_days`. The panel is outside the dock, so the dock stays one row on a phone. CSS hides it once `#actions` is on its way: one request at a time.
- Tests: five in `test_planning.py`, seven in `test_proposal.py` (two in Chromium, one at phone width), and one more from this review. The only existing tests touched are `test_planning.py`'s `_archive` and `_archived` helpers. Each gained an optional argument with the old default, so every earlier call reads the same.

## Findings and resolutions

| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f73-i-want-to-be-able-to-F1 | should-fix | claude | After pressing Set aside, a reload before the runner's pick showed the review page as if nothing had been asked: Set aside and Refresh back, pressable again. The owner's rule (2026-10-07) is that a request shows on its way wherever its result shows, and stops being editable. The thread page's Archive reads its pending request; the review page didn't. | `proposal_review` reads a pending `archive` "on" for the thread. The panel then shows "Setting aside at the runner's next pick" (dashed hazard edge, as the thread page's pill) instead of its buttons. Added `test_a_set_aside_on_its_way_shows_after_a_reload`. Resolved. |
| f73-i-want-to-be-able-to-F2 | nit | claude | The f73-02 escalation joined two CSS rules on one line in the phone block of `dashboard.css`. | Split again. Resolved. |
| f73-i-want-to-be-able-to-F3 | nit | backlog | `_put_aside` doesn't skip a merge whose card has left main (`_gone_merge`), as `_open_proposals` does. | `docs/backlog.md`. |
| f73-i-want-to-be-able-to-F4 | nit | backlog | The stale note shows on plans, mock-ups and replans only; an ADR or a merge never says its age, against the outcome's "a proposal that has waited". | `docs/backlog.md`. |

Checked and fine:
- D1: Set aside posts exactly the thread page's `archive` request. The runner's archive sets `archived_why` to `by you` (`runner/requests.py`), which `_put_aside` reads. An approval's archive (`approved`) stays under Archived, as tested.
- The rejected and applied cases each have a test. A pending archive already shows the desk card on its way (`coming.py`).
- The Refresh values are tested both in the HTML and as the posted row (`{"text": …, "comments": {}}`).
- `drafted_days` is measured from the latest lead message listing proposals. That message is where `find_proposal` finds the proposal unless it was replaced, and a replaced proposal shows no panel.
- Placement: the ticket and the card said "beside Approve". The lead put the panel just under the dock so the dock stays one row at 390 px, and the phone test checks 44 px and the page's width. That is a fair reading, not a finding.
- No French: the dashboard is English only.
- No screenshot (no browser in this job beyond the tests' Chromium).

No checkpoint read these tickets, so there are no checkpoint findings to judge. F1 was in a lead escalation's merge with no checkpoint after it, so none is marked missed.

**Score: 8 of 10.** The logic is right and read from what exists, as D1 asked. The tests are close to the Done when, with real presses in Chromium. One owner rule (on its way after a reload) was missed.

## Backlog
- F3 and F4, in `docs/backlog.md`.

## Workflow observations (Factory)
- **Flow:** two developer tickets, 0 of 6 attempts with an edit, two directions, two escalations, no stop, no park, no intervention by the owner. Both tickets were merged by Opus in one escalation session each.
- **Each model:** Qwen (qwen3.6-35b-a3b), 2 hours of model and no edit. Opus $4.58: escalations $3.48, which did the work, and directions $1.10, which changed nothing.
- **What to change:** bug-48 is already ready. Beyond it, the plan's "Who builds" should weigh the test file's size: both tickets sent Qwen into `test_planning.py` or `test_proposal.py` with Chromium fixtures. On a ticket with a browser test, F9's line already says to give it to the lead or split it. F73's plan didn't apply that line, so the next planner brief should check "D" tickets against the Known range in `lead.md` before queueing.
- **The review's own fix:** about 20 lines over three files plus a test, done by the lead rather than a ticket. It is a rule the owner set, Qwen has failed this file twice this week, and a ticket round would cost more than the fix.
