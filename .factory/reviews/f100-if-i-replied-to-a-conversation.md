# Review: F100, proposals show "being revised" while your reply waits for the lead

- **Status:** review round 1 done; waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
When you send a message on a thread that has open proposals, they stop asking for your review. On `/planning`, the card's box under "Proposals to review" turns dashed orange and says "being revised · {when the lead's reply comes}", and it no longer counts in the Planning tab's number or the desk's "waiting for you". On the thread page, each proposal in "Proposals from this card" gets a dashed orange edge and reads "being revised", at once when you press Send, with a line "The lead is revising these after your message." On a proposal's own page, a dashed "Being revised" line sits above Approve and Reject, which still work. When the lead replies, the proposals come back solid (or the new ones replace them). A proposal you had already approved or rejected keeps "on its way · the runner applies it at its next pick". Cancelling your message before the runner picks it up puts them back to solid.

### 2. How to test it yourself
1. On your phone, open a thread with open proposals (a card with a plan and a mock-up, say) and send a message.
2. Right away, on the thread page: both proposals on the right (below on a phone) have a dashed orange edge and say "being revised".
3. Open `/planning`: the card's box under "Proposals to review" is dashed orange, "being revised · …", and the Planning tab's number dropped by one.
4. Tap the box: the proposal's page shows the dashed "Being revised" line above Approve and Reject.
5. Wait for the lead's reply: the proposals are solid again (or replaced by the new ones), and the tab's number goes back up.
6. Optional: send a message, cancel it from the thread before the runner's pick: the proposals go solid within a few seconds.

### 3. Left for later
Nothing from this card.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-28 22:48 ([session](../sessions/2026-10-28-2248.md)): 1 ticket, `f100-01-proposals-being-revised`, built by Claude Sonnet as a lead ticket, merged first time in 12 minutes for $0.93; 0 local tokens.
- Lessons: D1's "one rule" was done properly: f74-01's rule now lives in `_waiting_for_lead`, and the desk, the thread page and the proposal page all read it. Two things slipped: the general thread's proposals (each its own desk item, a separate code path) got the new rule with no test, and the "when the reply comes" words were computed by a second copy of `_answers_wanted`'s loop. The review added the test and folded the two copies into one helper. An edited test kept a name that its new assertion contradicts; the review renamed it.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** the dashed "on its way" pattern now covers messages, their thread's proposals, approvals, archives and sign-offs. F96 (newest threads first in "Your answers wanted") is still a good small next card. For tickets: when a decision applies to "the desk's proposals", the ticket should name both paths (a card's bundle and the general thread's single items), since the general thread is the one tests forget.

### 7. What clogged the factory line
- Nothing: one 12-minute job, first attempt, no limit waits, no stops for you.

## What was built
- `factory_dashboard/planning.py`: f74-01's rule lifted into `_waiting_for_lead` (via `_waiting_order` and `_last_messages`, which `_answers_wanted` reuses unchanged) (D1). `_revising` words each waiting card "being revised · {next reply}"; `_open_proposals` and `_bundle` make a waiting card's open proposals dashed with those words, leaving an Approve or Reject on its way as `_NEXT_PICK` (D2, D3). Counts follow, as dashed items are out of `waiting_for_you` (D6).
- `factory_dashboard/thread.py`: `_proposals` gives an open proposal on a waiting thread the state `being revised`; `_standing` carries `revising` to the proposal page.
- Templates and CSS: the thread aside draws "being revised" with a dashed `--hazard` edge, keeping the kind's top border, and its foot line reads as in the mock-up; the proposal page shows the "Being revised" line above the buttons, which stay (D4); after Send, and on the 5-second poll when the conversation changes, the thread page redraws `#proposals` (D5).

Tests: five new tests in `test_planning.py` (dashed with a request or a stored message and an open planner job; solid again after a lead reply without proposals; solid after a cancel; an Approve on its way keeps its words; the thread and proposal pages). One existing test edited: `test_coming.py`'s Planning tab count test now expects the count to drop by one, f6's bundle, with a message waiting. That is exactly D6's intended change, not a weakening; the Needs you assertion is unchanged and right (the desk is one Needs you line whatever its count).

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The general thread's proposals (one desk item each, a separate branch in `_open_proposals`) got the new rule with no test | Fixed: `test_the_general_threads_proposals_are_revised_each_on_its_own` (`tests/factory_dashboard/test_planning.py`) |
| F2 | nit | claude | `_revising` repeated `_answers_wanted`'s per-card "when the reply comes" loop, two copies of one wording that could drift | Fixed: both read `_replies` in `planning.py` |
| F3 | nit | claude | `test_coming.py`'s edited test kept the name and docstring "the Planning tab count doesn't change" while asserting it drops | Fixed: renamed and redocumented |

No checkpoint ran (the only ticket was a lead ticket), so there are no checkpoint verdicts. Score: 8/10: D1–D6 built as planned, across three pages, with the refresh on Send and on the poll; one untested branch and some duplicated wording.

Checked and fine: the desk bundles a card's proposals into one item (F51), so "both proposals" in the card's Done when is one dashed box and the tab drops by one, as the test says; a cancelled message changes the conversation's stamp, so the thread page's poll redraws the proposals solid; Approve and Reject stay on the proposal page (the line is inside the open state only); the Overview's per-card proposal count is only worded for a "the lead replied" notice, which a waiting message has already answered. Ruff and mypy pass on the changed files. After the review's fixes, the desk's test files pass (`test_planning`, `test_coming`, `test_thread`, `test_proposal`, `test_overview`, `test_app`, `test_projects`: 523 tests). A full `tests/runner tests/factory_dashboard` run reached about 78% with no failure before the session's time limit stopped it; the runner's gates run the whole suite before merging.

The French: no `coucou/locale/fr/` change in this milestone. No browser here for screenshots; the template tests cover the classes and words.

## Factory
- Flow: one lead ticket on Sonnet, first attempt, no stops for the owner, no limit waits, no parks.
- Models: Claude Sonnet built it ($0.93); the local model had nothing to do. A lead ticket was right: it reads `planning.py`, `thread.py` and three templates.
- What to change: Sonnet again left an edge with no test (F74: an `ORDER BY`; here, the general thread's branch). Ticket writing: when a decision touches the desk's proposals, the Done when names the general thread as well as a card. Twice is near a pattern; one line in `docs/task-writing.md` if it shows a third time.

<!-- runner report -->
<!-- /runner report -->
