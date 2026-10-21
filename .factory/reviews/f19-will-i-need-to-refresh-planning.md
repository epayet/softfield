# Review: F19, the Planning desk and an open thread refresh by themselves

- **Status:** done, signed off by the owner on 2026-10-21.

## Sign-off sheet

**Expected:** the lead's answer shows up on the Planning desk and on an open thread by itself, within about 5 seconds, without you reloading and without ever wiping what you are typing. The Overview makes one request every 5 seconds instead of four.
**Done when:** with `/planning/<card>` open, a new lead message appears within a poll, and the desk moves the card to its new group; text typed in the reply box, a point's comment or the Plant box is never replaced by a refresh; the Overview's Needs you, Now, Queue and allowance refresh from one `/live` request every 5 s.

### 1. What changed
- **The desk refreshes itself.** On `/planning`, a card moves to its new group within about 5 seconds when the lead answers or the runner takes something: a seed the lead replied to moves up to "Your answers wanted" with no reload.
- **An open thread refreshes itself.** Leave a card's page open after sending: the lead's answer appears in the conversation by itself, its points one at a time on the phone as usual. The page is only redrawn when something new was written, so an open "Full reply" doesn't close every 5 seconds. (Built in this review: the three tickets had left the thread out.)
- **Nothing you type is lost.** Every live page waits while a text box has the cursor, holds text you typed, or a waiting plant is open for editing; it also waits for a comment you typed on a point and folded away, since that comment is still sent with your message.
- **The Overview polls once.** Needs you, Now, Queue, the allowance and the top bar now come from one request every 5 seconds instead of four.

### 2. How to test it yourself
1. On the phone, open a card's thread, send a short message, and leave the page open. When the lead answers, its message appears without a reload.
2. Before it lands, start typing in the reply box. Nothing changes under your fingers. Empty the box and tap outside it: the answer appears within a few seconds.
3. Open "Comment…" on a point, type a few words, close it again. The page still waits; press Send and the comment goes with the message.
4. Open `/planning` on the laptop and leave it. When the runner answers a card, the card moves group by itself.
5. On the Overview, watch Now and the Queue change when a ticket starts or finishes, without a reload.

I couldn't open the real dashboard from this job; each step is covered by a browser test on the fixture database.

### 3. Left for later
Nothing new. The poll on every other page (the top bar's) still runs while you scroll or type, as before F19; it only updates the top bar, so it can't wipe anything.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-07: you planted the question; planned the same week as two developer tickets.
- 2026-10-14 (no session report: the run was interrupted, see b1b6bec): f19-01 merged at the first attempt, 45 min of model, 5.9M local tokens.
- 2026-10-14 20:56 ([session](../sessions/2026-10-14-2056.md)): f19-02 merged on its third attempt after a direction, 160 min of model, 10.3M local tokens.
- 2026-10-15 00:23 ([session](../sessions/2026-10-15-0023.md)): the checkpoint found f19-02 untested where it mattered and wrote f19-03; it merged on its third attempt, 88 min, 8.6M local tokens.
- 2026-10-15 07:35 ([session](../sessions/2026-10-15-0735.md)): the second checkpoint passed f19-03 with one nit.
- 2026-10-21: this review, round 1. Three fixes by the review, no ticket.
- Lessons:
  - **The headline wasn't in any ticket.** f19-01 said "the thread's poll is the lead's", and no lead ticket was written. Three tickets and two checkpoints later, the first thing you asked for wasn't built. Every Done-when line needs a ticket carrying it (F14 and F106 said the same).
  - **A shared partial is shared.** f19-02 put "swap me" markers in `/live`'s sections, which every page fetches. On every page but the Overview that logged three errors every 5 seconds. Now only the Overview's poll asks for those sections.
  - **"Visible" was too broad.** The ticket said a typed *input* counts only when visible; the code skipped hidden *textareas* too, which a folded comment is.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - A plan check that each Done-when line is named by a ticket's Done when. This is the third milestone where an outcome fell between tickets (F14, F106, F19). Worth a planted card:
    > Plans: every Done-when line of a card is carried by at least one ticket's Done when, checked when the plan is approved, so no outcome falls between tickets.
  - Checkpoints on template work should list the other pages that include a changed partial; a one-line addition to the checkpoint brief.

### 7. What clogged the factory line
- **Seven days from the note to the first merge** (planted 2026-10-07, f19-01 merged 2026-10-14): the queue's order, and f19-01 held behind f12-03 (the red main of 2026-10-10).
- **Failed attempts:** five of six failed developer attempts were "no edit after 10 minutes" or a timeout. About 3 hours of model time on f19-02 and f19-03 together for roughly 10 lines of template; the lead would have done both in minutes. Unclog: the routing rule from F14/F30 (template-and-script tickets on these pages go to the lead) applies here too.
- **A review that stopped on nothing:** the first review of this card stopped at once with "end-to-end tests fail on staging" (a project with no end-to-end tests); f135-01 fixed that, and this review is the rerun. About six days between.
- I couldn't query the metrics database from this job; the hours are from the session reports and git.

## What was built
- **f19-01** (`planning.html`, `base.html`): two `display: contents` wrappers poll `/planning` every 5 s while `liveIdle()`, one around `#desk`, one around `#desk-coming` (inside its `if`), each with `hx-disinherit="hx-select"` so the desk's own buttons still draw their answers. `window.liveIdle()` now also waits while a field has focus, while a text box differs from what the page gave it, and while a `details` holding a field is open.
- **f19-02** (`overview.html`, `base.html`, the three partials): the Overview's four polls became one; `base.html`'s `#live-poll` is a block the Overview empties.
- **f19-03** (`test_overview.py`): a browser test that the one poll refreshes Now, Queue, the allowance, Needs you and the top bar; it removed a stray `hx-swap-oob` from the poller.
- **The review** (`thread.html`, `deck.js`, `base.html`, `overview.html`, the partials): the thread's poll (F1), the out-of-band pick moved to the Overview (F2), and folded comments counted (F3). Five tests.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | blocking | claude | An open thread had no poll: the lead's answer still needed a reload, against the card's first Done-when line. f19-01 left it "to the lead" and no ticket was written | Fixed: `#conversation` holds a hidden stamp of what the runner and lead wrote; every 5 s, while `liveIdle()`, the page is read again and the conversation swapped only when the stamp changed. `deck.js` binds each deck once and again after `htmx:afterSettle`, so redrawn points stay one-at-a-time (the send's own redraw had the same gap). Tests: the answer appears; it waits while the reply box holds text |
| F2 | should-fix | claude | f19-02's `hx-swap-oob` on `/live`'s Now, Queue and allowance sections made every other page's top-bar poll log `htmx:oobErrorNoTarget` three times every 5 s | Fixed: the sections carry nothing; the Overview's poller has `hx-select-oob="#now:innerHTML,#queue:innerHTML,#allowance:innerHTML"`. f19-03's browser test still passes; a new test pins the markup |
| F3 | should-fix | claude | `liveIdle` skipped hidden textareas, so a comment typed then folded (or on a point the phone deck moved off) didn't hold the refresh, and a redraw would lose it | Fixed: only hidden inputs are skipped. Test: a folded comment keeps the page from counting as idle |

Checkpoint findings:
- **C879-1** (no test that the desk poll moves a card): confirmed. The review added `test_the_desk_poll_moves_an_answered_seed_to_the_answers`.
- **C879-2** (the poll URL repeated `&project=coucou`): confirmed, and worse than a nit: on any other project the desk would have been replaced by Coucou's. Already fixed on main by ADR 30's session (34b1cd7).
- **C892-1** (the Overview's single poll was only counted): confirmed; f19-03 fixed it.
- **C907-2** (stale comment above the poller): confirmed; rewritten with F2.
- Missed by the checkpoints: F2 (C892 read f19-02's partials) and F3 (C879 read f19-01's `liveIdle`).

Read and found sound, no finding:
- **Edited existing tests.** f19-02 excluded `/` from `test_app.py`'s every-page poll check (the Overview has its own poll now; f19-03's browser test covers it) and replaced a count of four polls by one. Both are honest changes, nothing weakened.
- **The desk's buttons** keep drawing their answers inside the poll wrappers (`hx-disinherit`); `test_dismiss_takes_the_item_off_at_once…` still passes unchanged.
- **The waiting plant's editor** arrives filled; its value equals its default, so it doesn't hold the page.

Checks: `uv run pytest -q tests/runner tests/factory_dashboard` gave 2461 passed after F1 and F2. F3's one-line change and the last two tests came after, and the 24 live-page, thread and Overview tests around them passed. Ruff is clean on both edited test files.

French: nothing to check, no `coucou/locale/` file changed. Screenshots: no browser of my own in this job; the browser tests drove Chromium.

Score: 6/10. f19-01 was clean and right first time, and the polling design (one request, gated by `liveIdle`) is sound. It lost points for the headline left unbuilt, the errors on every page, and two tickets that needed three attempts each for a few lines.

Stop reason: none.

## Factory
- **The flow:** three developer tickets, one direction, two checkpoints (both useful: C892 caught that f19-02 was untested and wrote f19-03). No escalation, no stop for you during the build. The first review stopped on the staging rule for a project with no end-to-end tests (fixed by f135-01).
- **Models:** Qwen 1/3 first time, 24.9M tokens, five of six failed attempts no-edit stops or timeouts. Claude: the checkpoints on Sonnet, this review on Opus; see the numbers below.
- **What to change:**
  - Plans: each Done-when line is carried by a ticket (card text above, for you to plant).
  - Checkpoint brief: for a changed partial, name the pages that include it. A one-line change, for the next planning session.

## Workflow observations
- f19-01's run left no session report (interrupted, and its branch recovered); its numbers are from the commit trailer.
- The milestone's start tag predates ADR 30's move, so `git diff …-start..main` covered 500+ files of other work; the review read the three f19 commits instead (bug-01's case again).

<!-- runner report -->
<!-- /runner report -->
