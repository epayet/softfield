# Review: F22, Archive sits at the bottom of a thread

- **Status:** done, signed off by the owner on 2026-10-14.

## Sign-off sheet

**Expected:** your note was "move the archive button on a planning thread to the bottom rather than the top". On a card's thread the top shows only the card's name; Archive (or Unarchive) and, on a seed, "Remove seed" sit at the bottom of the page, under the reply box, where you are once you've read the thread to the end.
**Done when:** the Archive row comes after the conversation and the reply box, on a phone and a desktop; on a phone the Send box still sticks while you read and Archive shows once you scroll to the end; "Remove seed" moves with it; everything else about archiving is unchanged.

### 1. What changed
- On a card's thread, the top is the card's name and nothing else. Archive (or Unarchive) is now the last thing on the page, under the reply box.
- "Remove seed" moved with it, just above Archive, so no button that ends a card sits at the top any more.
- On a phone the Send box still stays at the bottom of the screen while you read. Archive is out of view until you reach the end, then shows under Send.
- Nothing else about archiving changed: pressing it still shows "Archiving at the runner's next pick" with a dashed orange edge, the button goes, and a reply opens the thread again.

### 2. How to test it yourself
1. On your phone, open the planning room and a thread with a few messages.
2. Look at the top: the card's name only, no Archive, no "Remove seed".
3. Scroll down: Send stays at the bottom of the screen while you read.
4. Scroll to the very end: Archive shows under the Send box.
5. Open a seed nobody has planted yet: "Remove seed" is at the bottom too.
6. If you have a thread you no longer need, tap Archive: the button goes and "Asked" shows in its place; reload, and the dashed "Archiving at the runner's next pick" is there.

I didn't look at it on a screen myself: a review job has no browser to look through. A test opens it in Chromium at a phone's width and measures where Send and Archive are, before and after scrolling to the end.

### 3. Left for later
- Backlog: "Remove seed" and Archive are two stacked lines where the ticket asked for one row, with a few pixels of extra space above Archive. Only a seed that already has a conversation shows both. To tidy when the bottom of the page next changes.
- F30 (newest answer first) may reorder the thread. If it does, Archive stays at the very bottom, and F30 updates the position tests (D3).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-07: planted by you, and planned with one developer ticket.
- 2026-10-13, evening: f22-01 built by the local developer (Qwen) and merged at its first attempt: 31 minutes of model, 15 of gates, 2.4 million tokens read, no Claude support. I found no session report for that run in `docs/sessions/` yet; the figures are from the merge commit (`5db9e21`).
- 2026-10-14: this review, round 1. One test added by the review, one backlog line, no ticket.
- Lessons:
  - The developer did exactly what the ticket's Done when said, and the ticket's Done when left out the one thing that needs a browser: the sticky Send box on a phone, which is why the row went where it did. A ticket for a move made because of how the browser lays something out now carries one browser check (written into "Known range" in `docs/agents/lead.md`).
  - A one-sentence request took six days to reach you, and under an hour to build. It waited behind a red main and its turn.
  - The review read 31 files to find one commit, the third time in two days.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Run bug-01 (ready, a lead ticket) before the next reviews: each review of a small card pays to read everyone else's work.
  - Small, one-file tickets like this one could pass ahead in the queue when a developer is free: they are the cheapest way to answer one of your notes the same day. Worth planting as a card if you agree; text ready to paste: "Small tickets first: when a developer is free, a difficulty 1–2 ticket with one file goes ahead of longer ones, so a one-line note doesn't wait six days. Open question: does it ever starve a big ticket?"
  - F30 will touch this page next; its ticket should name the three position tests it changes.

### 7. What clogged the factory line
- **Six days between your note and the merge** (2026-10-07 to 2026-10-13), none of it in the work. The ticket depended on f12-03, the lead ticket that made main green again, and then waited its turn. What unclogs it: small tickets first (above), and F13's lesson, already written down, that developer tickets wait while main is red.
- **15 minutes of gates for 59 lines**, a third of the ticket's time. What unclogs it: F71's slow-tests study (f71-02, ready).
- **The review:** four minutes for the three test folders, and 934 lines to sort for 59. What unclogs it: bug-01.
- I couldn't read hours from the metrics database in this job (a headless review has no query command); the figures are from the commit and git. The fix is in the backlog (f53-review: a "where the hours went" block in `runner report`).

## What was built
- **The page** (`factory_dashboard/templates/thread.html`): the `#remove-seed` block and the `#archive` row left `<header id="card">` and now follow `#conversation`'s closing tag, in the same column. Ids, `hx-` attributes and conditions are unchanged, so every request they post is the same.
- **Tests** (`tests/factory_dashboard/test_planning.py`), by the developer:
  - the Archive button comes after the reply box, and the header holds neither it nor "Remove seed";
  - on a seed, the Remove button comes after the reply box;
  - new: while a reply waits (no form), the Archive row still shows, after the waiting line.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | Nothing tested the phone half of Done when (Send still sticks, Archive shows under it at the end), nor that the "on its way" pill is in the new place. The developer's tests compare positions in the HTML text | Fixed in the review: `test_on_a_phone_archive_shows_under_send_at_the_end_of_the_page`, in Chromium at 390 × 500 on a seven-point thread, and one position assertion in `test_an_archive_on_its_way_shows_at_once_and_its_button_goes`. Both pass on the merged template: the code was right |
| F2 | nit | backlog | "Remove seed" and Archive are two stacked blocks, not the one row the ticket asked for, and `#archive` keeps the header's `margin-top: 6px` | `docs/backlog.md` |
| F3 | nit | backlog | Round 1 was handed 31 files and 934 lines; F22's is one commit of 59. Third time (f79-F3, f104-F2) | Already a ready ticket, `tasks/ready/bug-01-review-reads-its-own-commits.md`; no new one |

Read and found sound, no finding:
- **D1 holds.** `.dock` is `position: sticky; bottom: 0` under 640 px, and a sticky box stays inside its parent, `#conversation`. The row is after that parent, so it can't be covered once the page is scrolled to the end; the new test measures it.
- **A reply doesn't lose the row.** A sent reply reloads `#conversation` only; the row is outside it, as it was in the header.
- **Nothing else moved.** The diff of `thread.html` is the two blocks taken out and put back with two spaces less indentation.

Edited existing tests: two, both by additions only. `test_only_a_seeds_thread_has_remove_seed` gained one position assertion; `test_a_threads_button_archives_it_and_an_archived_ones_opens_it_again` gained four and a docstring. No assertion was removed or loosened.

Not reviewed here: the rest of the range, which is F14's escalation (f14-02, the editor for a waiting plant), a direction on f19-01, F114's plan, and a terminal session's work on the runner (gates run again after a stop, longer timeouts) and on the roadmap. Each belongs to another milestone's review or to that session.

No checkpoint finding was handed to this review, so there is none to judge. French: nothing to check, no user-facing string and no `coucou/locale/` file changed. Screenshots: no browser to look through in this job. After the fix, `uv run pytest -q tests/unit tests/integration tests/runner` gave 1881 passed, 1 skipped; the nine archive tests in `tests/factory_dashboard/test_planning.py` pass, the Chromium ones included; ruff is clean on the edited file.

Score: 9/10. The smallest change that does it, at the first attempt, with tests that hold the order. It lost a point for tests that never opened the page at a phone's width, when the phone is the reason the row sits where it does.

Stop reason: none; nothing is left for a round 2.

## Factory
- **The flow:** one developer ticket, merged first time. No stop, park, limit, direction or escalation on F22 itself.
- **Models:** Qwen (qwen3.6-35b-a3b) for the ticket; Claude Opus for this review. See the numbers below.
- **What to change:**
  - A review reads its own commits (F3, bug-01).
  - A ticket for a layout move carries one browser check (F1; in "Known range").
  - Small one-file tickets could go first when a developer is free (sheet, item 6).

## Workflow observations
- The f22-01 run's session report wasn't in `docs/sessions/` when this review ran (the newest there is 2026-10-13 16:20, the merge is 20:22). If the run was still going, it will come; if not, a run that reaches a review should write its report first.
- 2.4 million tokens read to move 31 lines: the developer re-reads `thread.html` and the 2,400-line test file at each step. It costs nothing in dollars, and it is most of the 31 minutes.

<!-- runner report -->
<!-- /runner report -->
