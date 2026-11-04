# Review: F170, blocked tickets and the lead's fix

- **Status:** done, signed off by the owner on 2026-11-04.

## Sign-off sheet

### 1. What changed
- **A blocked ticket on the desk now offers the lead's fix.** It shows the lead's first point, the replan's title and how many key points it has, with "Approve the lead's fix" as the yellow button. "Try again as it is" and "Set aside" are the quiet ones, and a line says what Try again does to the fix.
- **Pressing Try again no longer spoils the fix.** You can still approve the lead's fix afterwards: its version replaces the ticket Try again put back. This is the "I keep trying to approve it and it keeps coming back" you planted.
- **A blocked ticket's page explains itself.** A Blocked panel gives the reason and the lead's fix, has the same three buttons, and links to the card's thread and the card.
- **Every ticket page's first crumb names its card** ("F21, The lead's briefs") and opens the card's page.
- **While the lead is still reading,** the plate says so and there is nothing to approve yet.
- **A bug ticket** keeps its two plain buttons, "Try again" and "Set aside".

### 2. How to test it yourself
On a phone and on the computer, the next time a card's ticket is blocked. It can't be tried before one is.
1. Open `/planning`. Under Blocked tickets, the words give the reason and how many tickets wait behind it. Right after the block, the plate says the lead is reading.
2. When the lead has replied with a replan, the plate shows its first point and title, and the yellow button is "Approve the lead's fix".
3. Tap the ticket's name. The page has the Blocked panel, the same buttons and both links. The first crumb opens the card.
4. Press "Try again as it is", then approve the fix from the card's thread at the next chance. It should be approved, saying the lead's fix replaced the ticket.
5. On another block, press Approve and reload the page. The item stays dashed orange with no button, until the runner's next pick.

### 3. Left for later
- **bug-57** (new): pre-flight refuses a developer ticket that spans two pages.
- **bug-49** (already set aside, extended here): a third timing test failed once in this review's run, then passed when run again.
- **bug-25** (already set aside, reworded here): any lead message after the runner's look counts as the lead's reply, so an answer to another question can end "the lead is reading" too early. I suggest bringing it forward: it matters more now that the plate is on the desk.

### 4. Decisions waiting for you
None.

### 5. How the work went
- **2026-11-02 22:10** ([session](../sessions/2026-11-02-2210.md)): f170-02 merged by Sonnet in about 6 minutes for $0.35.
- **2026-11-03 11:05** ([session](../sessions/2026-11-03-1105.md)): f170-03 merged by Qwen first time. f170-04 failed three times and Opus finished it.
- **2026-11-03 14:33** ([session](../sessions/2026-11-03-1433.md)): the two fix tickets merged by Qwen, f170-05 on its second attempt.
- **2026-11-03 review:** nine findings fixed by the lead, one set aside, two only reported.

Lessons:
- **A finding with several parts gets fixed in part.** f170-05 was given three problems in one paragraph and left the words and the label as they were. f170-06 then wrote the wrong label into a test. Next time, each part should be its own Done when line. My suggestion is to have the checkpoint's fix tickets do this.
- **Checkpoints trusted the fix tickets and their tests.** The second said f170-05 and f170-06 covered the problems, and the third said the screen matched the ticket, while the ticket's own lines still failed.
- **Made-up threads hide real ones.** Every test had one lead reply, but real threads carry more, including "Approved by the owner…" as a lead message. Any later message made the Approve button disappear. Those cases are now tested.
- **f170-04 should have been the lead's from the start.** It spans two pages' modules. A rule alone has now failed three times, so it becomes a check (bug-57).

### 6. What next
- **Product:** nothing from this card; product work stays on hold, as you asked.
- **Factory:**
  - Bring bug-25 and bug-57 forward, for the reasons above.
  - Split a checkpoint finding's parts into separate Done when lines on its fix ticket.
  - Your next blocked ticket is the real test: look at it on the phone.

### 7. What clogged the factory line
From the metrics database's jobs, for this card's tickets only:
- **f170-04's failed attempts, 2 h 03:** Qwen ran 75 minutes to a timeout, 28 minutes to a mypy failure, and 20 minutes with no edit; the direction and escalation took 18 more on top. To unclog it: bug-57 sends this kind of ticket to the lead at once.
- **f170-05's first attempt, 20 minutes:** stopped with no edit. Its second took 42 minutes for 17 changed lines. To unclog it: the lead fixes small findings of this kind directly when they touch a page's template and module together.
- **f170-03 waited overnight, about 11 hours (00:09 to 11:06):** the session before it ended with "Claude changed runner/, so the runner needs a fresh process", and the next run began at 11:05. To unclog it: I suggest looking at a runner that restarts itself after that stop, in the next planning session, beside bug-05.

<!-- runner report -->
<!-- /runner report -->

## What was built
- **f170-02:** `_approve_plan` in `runner/requests.py` settles the clash with a ticket Try again put back, in favour of the replan's version, with the blocked run's footers carried over. A running ticket and any other clash are refused as before.
- **f170-03, f170-05, f170-06:** the desk's blocked item with its plate and three buttons.
- **f170-04:** `get_blocked_info` as the one lookup for the desk and the ticket page, the Blocked panel, and the crumb.

## Findings and resolutions
All fixed by the lead in round 1 unless noted. Each is under about 20 lines per file; F2 to F4 repeat what f170-05 had been asked to fix.

| Id | Grade | What | Resolution |
|---|---|---|---|
| F1 | should-fix | After Approve, a redraw of the desk brought the buttons back, because `_acted_on` didn't know `approve_plan`. The owner could press it again. | `_acted_on` marks the item on its way; tests added. |
| F2 | should-fix | The desk's words still ended "· the lead is looking at it" or "· the lead's fix waits on F9's thread", which the plate now says. Part of checkpoint C1695-1, never done. | `words` removed; the desk shows the reason; two tests corrected. |
| F3 | should-fix | The desk's button read "Try again as it is" on a ticket with no card, and f170-06 wrote that into a test. | Label follows the card; test corrected. |
| F4 | should-fix | The regex cut everything after "its work is on task/", so "· 1 ticket waits behind it" was lost on real items such as f152-01. | Only the branch clause goes; test added on the real text. |
| F5 | should-fix | The fix was read from the lead's latest message, not the latest listing proposals, so any later lead message hid Approve though an approval would still work. | Reads the latest reply listing proposals after the look; test added. |
| F6 | should-fix | A replan rejected, sent back or approved was still offered while the item stayed open, and Approve would be refused. | Offered only while open or on its way, using `proposal_state`; parametrised test added. |
| F7 | should-fix | The ticket page still said "the lead is reading" for a reply with no points. f170-05 fixed this on the desk only, an hour after f170-04 merged. | Page uses `lead_replied`; test added. |
| F8 | nit | The desk's thread links dropped the project (`q`); a replan with no points hid its title though Approve showed; "1 key points". | All three fixed; the plate's branches simplified. |
| F9 | should-fix (route: later) | Pre-flight doesn't refuse a developer ticket that spans two pages' modules. | bug-57 set aside. |

**Checkpoints:**
- C1695-1 confirmed; only its third part was done before this review.
- C1695-2 confirmed.
- C1709-1 confirmed, though the checkpoint judged it "not worth a ticket": it's a one-line test, now added.

**Tests read closely:** the two edited tests had their assertions corrected, as above. `test_tickets.py`'s new tests are sound. They read the panel's own section, and the f170-02 tests run real git merges.

**French:** nothing to check; no file under `coucou/locale/` changed.

## Only reported
- A replan moving the running ticket to later/, after a Try again on it, isn't refused by name: the move of that later/ ticket into ready/ raises, and the approval is undone by the error path. It would take a Try again on a ticket that's running, and nothing is lost.
- `get_blocked_info`'s item query ends `ORDER BY created, id DESC LIMIT 1`, a mixed order. An open item is unique per subject, so it has no effect.

## Workflow observations
- **Fix tickets name too little:** f170-05's `files:` listed only `planning.py`, and it had to change `coming.py` and `planning.html`. A checkpoint's fix ticket lists only the finding's file.
- **The repaired ticket got a fact wrong:** the direction on f170-04 said nothing counts the tickets behind a blocked one, but `blocked_text` in `runner/loop.py` does. The escalation noted it; the page's reason does carry the count.
- **Copilot as stand-in:** its C1695 findings were the most precise of the three checkpoints and all held. The Sonnet checkpoints that followed passed the fixes on reading their tests.

## Test run
`tests/runner` and `tests/factory_dashboard` on 16 workers: 2,965 passed, 1 failed. The failure is `test_a_pause_lets_the_job_finish_then_holds_until_the_owner_resumes`, whose sleeps had an extra `0.001`. It is in the runner's pause loop, which this review didn't change, and it passed alone and with its whole file on 16 workers (331 passed). I didn't find what made that sleep, and it's added to bug-49. A run on one worker didn't finish within its time limit, and the suite hasn't been run again from start to finish since.

## Factory
- **Flow:** no stop for the owner. One escalation, one direction, and the f170-05 no-edit stop.
- **Models:**
  - Sonnet merged the protected lead ticket first time for $0.35.
  - Qwen managed one-module tickets and small test fixes, and failed the two-page ticket.
  - Opus finished that ticket for $1.94, plus $1.24 for its direction.
- **What to change:** bug-57, and fix tickets with a Done when line for each part of a finding, as above. I haven't written a ticket for the second: it needs a look at how the checkpoint writes them, so it belongs in the next planning session with the owner.
