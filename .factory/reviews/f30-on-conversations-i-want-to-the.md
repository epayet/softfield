# Review: F30, a thread shows the latest answer first

- **Status:** done, signed off by the owner on 2026-10-16.

## Sign-off sheet

**Expected:** your note was "on conversations, I want the latest answer first so that I don't have to scroll". A card's thread opens on the lead's latest answer, at the top; Send sits right under its points; the older messages fold under "Earlier in this thread (N)", newest first, one tap away.
**Done when:** on a phone, a thread with several exchanges shows the lead's latest answer and Send on the first screen, and Earlier opens the older messages newest first; a reply you send shows at the top, dashed orange, without a reload.

### 1. What changed
- A card's thread now starts with the lead's latest message, with its points and Comment… boxes, and the Send box right under it.
- Everything older is folded under "Earlier in this thread (N)", newest first. Tap it to open.
- While a message of yours waits for the lead, "Next for the lead · …" and your waiting messages (dashed orange, newest first) come first, above the lead's latest message.
- A reply you send appears at the very top at once, dashed, without reloading.
- *(Fixed in this review)* When the lead's latest message has no points (a short answer, or the "Approved by the owner" note on every approved card), the Send box no longer says "6 points · 0 comments" about points hidden under Earlier, and those folded points have no Comment… boxes. You comment on what you see at the top.

### 2. How to test it yourself
1. On your phone, open the planning room and a card with a long conversation (F12 or F95 have 13–14 messages).
2. The first message under the card's header is the lead's latest one. Send is on the screen without scrolling.
3. Under Send, "Earlier in this thread (13)" is closed. Tap it: the messages are listed newest first, down to your first note.
4. On a card the lead has answered with points, type a short reply and press Send: it shows at the top, with a dashed orange edge and "Sent", and "Next for the lead" above it.
5. On F95: the top is the "Approved by the owner" note, and the Send box says nothing about points.

One thing that still needs a scroll: a card with a written review (F95, for example) shows the review's sheet first, above the conversation. That is in the backlog (fold the sheet once the card is signed off).

### 3. Left for later
- Backlog (new): on a reviewed card, the review's sheet comes before the conversation, so on a phone the latest answer is below the fold. Suggested: fold the sheet into a closed "The review · signed off <date>" once it is signed off.
- Backlog (already there): after Send, the page reloads the conversation with an `innerHTML` swap, which nests a second `#conversation` inside the first (f14-F3). Nothing shows wrong; F30 didn't touch it.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-07: planted by you and planned with one developer ticket, f30-01 (difficulty 3).
- 2026-10-16, 04:40, 130 minutes ([session report](../sessions/2026-10-16-0440.md)): the local developer (Qwen) tried three times on 7.8 million tokens. Twice it stopped after 10 minutes of reading without writing anything; the third time, after a direction from the lead, it copied the message's HTML a second time instead of reusing it, lost the Comment… boxes and bent seven existing tests to fit. The lead threw that branch away and did the ticket itself on main: about 20 lines of template, a 5-line split and nine test updates, plus three new tests.
- 2026-10-16: this review, round 1. Two fixes by the review, one backlog line, no ticket.
- Lessons:
  - **The ticket should never have gone to the developer.** It was planned on 2026-10-07; on 2026-10-14 F14's review ruled that planning-page tickets adding to the 2,700-line `test_planning.py` are the lead's, and nobody went back over the tickets already waiting. The escalation wrote the lesson down ("Known range" in `docs/agents/lead.md`) and listed 16 more waiting tickets in the same case; this review moved all 16 to the lead.
  - **Tests that pass on made-up data missed a case real data has on every approved card.** The tests' latest lead message always had points; F95's real thread ends with an approval note, which showed the leftover "6 points" counter. Reading one real page (`softfield look page /planning/f95`) found it in a minute.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - With 16 more tickets now the lead's, Claude's share of the queue grows. Splitting `test_planning.py` (by page: the desk, a thread, proposals) would let the developer take planning-page tickets again; worth planting. Text ready to paste: "Split test_planning.py by page (desk, thread, proposals, plant), so the local developer can take planning-page tickets again instead of the lead. Open questions: one file per page or per feature? Does the split need its own ticket before the 16 lead tickets run, or can it go after?"
  - A review should open the real page with `softfield look page` before reading the tests: it is the cheapest check against tests built on tidy data (F109's lesson, again here).

### 7. What clogged the factory line
- **130 minutes on a ticket the lead finished in a few minutes of edits.** Two 10-minute no-edit stops, then a third attempt that had to be thrown away. What unclogs it: the routing rule applied to what is already waiting (done in this review for 16 tickets), and a split of `test_planning.py` (above).
- **Nine days between your note and the merge** (2026-10-07 to 2026-10-16), spent waiting its turn behind higher priorities, none of it in the work.
- The minutes come from the session report; the review job can't read the hours per wait from the metrics database beyond what `softfield report` writes below.

## What was built
- **`thread_page`** (`factory_dashboard/planning.py`): splits the thread at the lead's latest message. `messages` is now the latest group (what came after that message, newest first, then the message itself); `earlier` is everything before it, newest first. With no lead message, everything is in the latest group and `earlier` is empty.
- **`thread.html`**: one `draw(msg)` macro draws a message, used for both parts. Inside `#conversation`: `#waiting` first, the latest group, the merged-on block, the Send form and its script, then a closed `<details id="earlier">` with "Earlier in this thread (N)". `#reply` and its script stay inside `#conversation`, so the reload after Send still redraws it all.
- **Tests** (`tests/factory_dashboard/test_planning.py`), by the lead in the escalation: three new ones (the latest exchange, then Send, then a closed Earlier listing five messages newest first; waiting messages above the lead's latest one, dashed, with no Send; no Earlier for a lone lead message or a lone waiting message) and nine updated for the new order.
- **By the review:** `_messages` marks a message `latest` (the one with Comment… boxes, and the points counted by Send) only when it is the lead's last message and has points.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | When the lead's latest message has no points, Comment… and "N points · 0 comments" still followed an older points message, now folded under Earlier. On F95's real page: the approval note at the top, "6 points · 0 comments" by Send, the boxes hidden | Fixed: `_messages` (`factory_dashboard/planning.py`) marks only the lead's last message, when it has points. One assertion added to `test_the_latest_exchange_comes_first_and_the_older_messages_fold_newest_first`, which fails without the fix |
| F2 | should-fix | claude | 16 ready developer tickets add tests to `test_planning.py`, against F14/F109's rule, the very cause of F30's failure; the escalation left them for "the next lead session" | Fixed: `agent: lead` on f26-02, f32-01, f33-02, f42-01, f51-01, f63-01, f65-03, f67-02, f73-01, f73-02, f74-01, f75-01, f90-01, f106-03, f108-01, f112-01 |
| F3 | nit | backlog | On a reviewed card, `#review` sits above the conversation, so on a phone the latest answer is below the fold | `docs/backlog.md` |

Read and found sound, no finding:
- **The split.** `split = -1` with no lead message gives `messages[0:]` reversed and an empty `earlier`; a lead message last gives an empty "after" part and the message alone. Waiting messages are appended after the stored ones, so they always land in the latest group.
- **One macro.** Jinja macros see the page's variables (`project`, `next_reply`), so the waiting message's Edit/Cancel and the point boxes behave as before; ids are per message, so nothing repeats.
- **F22's Archive** is still after `#conversation`, so it stays the last thing on the page, under Earlier; its phone test passes.

Edited existing tests (nine, in the escalation, though its note says six): `test_a_fixture_reply_with_7_points_shows_each_point`, `test_a_reply_with_points_folds_its_text_and_one_without_shows_it`, `test_send_with_comments_posts_one_request`, `test_a_waiting_message_has_edit_and_cancel_it_and_a_stored_one_neither`, `test_an_edit_on_its_way_shows_the_new_message_and_no_buttons`, `test_an_edit_the_runner_will_refuse_keeps_the_messages_words`, `test_a_cancel_on_its_way_strikes_the_message_and_the_send_form_comes_back`, and the two browser tests of Save and Cancel it. Each swaps an order (`.last` to `.first`, unpacking reversed) for the new newest-first order; none was loosened. The one that changed shape, "the fold comes before the deck", now checks the deck is inside the same message after the fold, which is what it meant. `test_send_with_comments_posts_one_request` gained a check that the first message is the one just sent.

No checkpoint ran on this milestone (the ticket was finished by the lead in an escalation), so there is no checkpoint finding to judge. French: nothing to check, no `coucou/locale/` file changed. Screenshots: no browser in this job; the page was read as text with `softfield look page`. After the fixes: `uv run pytest -q tests/runner tests/factory_dashboard` gave 2306 passed, ruff and mypy clean on `factory_dashboard`.

Score: 7/10. The final code is small and right, with good tests of the order. It loses points for three failed developer attempts on a ticket that was the lead's by an existing rule, and for tests that never had a lead message without points last, the commonest real ending.

Stop reason: none; nothing is left for a round 2.

## Factory
- **The flow:** one developer ticket, three attempts (two no-edit stops, one after a direction that failed its gates and was a poor branch), then an escalation that reset and did it (the owner's "prefer reset" rule followed). No park, limit or stop for the owner.
- **Models:** Qwen (qwen3.6-35b-a3b) on all three attempts, 7.8M tokens in; Claude Opus for the direction, the escalation and this review. Dollars in the numbers below.
- **What to change:**
  - When a routing rule is added, re-route the waiting tickets it covers at once (written into "Known range" by the escalation; done here for the 16).
  - Split `test_planning.py` so planning-page work can go back to the developer (planted-card text in the sheet, item 6).
  - Reviews open the real page with `softfield look page` early (F1 was found that way).

## Workflow observations
- The session report's narrative is still "Not written by the runner"; this review is the narrative for the 04:40 session.
- `softfield look page` is now the review's best stand-in for a browser: one command read F95 exactly as the owner sees it and showed F1.

<!-- runner report -->
<!-- /runner report -->
