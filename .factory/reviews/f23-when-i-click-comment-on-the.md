# Review: F23, "Comment…" puts the cursor in the box

- **Status:** reviewed, round 1; waiting for your sign-off.

## Sign-off sheet

**Expected:** your note was "I currently need to click on both Comment and then click on the box to start typing". Tapping "Comment…" under a point of the lead's reply on a planning thread opens the box with the cursor in it, so you type at once; on a phone the keyboard comes up.
**Done when:** one tap on a point's "Comment…" opens its box with the cursor in it; a second tap closes it, as today, and keeps what you typed.

### 1. What changed
- On a planning thread, one tap on "Comment…" under a point opens its box and puts the cursor in it. No second tap on the box.
- Tapping "Comment…" again still closes the box, and what you typed is still there when you open it again.
- It keeps working after you send a reply and the conversation reloads in place.
- Nothing else on the page changed; the proposal review page already worked this way.

### 2. How to test it yourself
1. On your phone, open the planning room and a thread whose last reply from the lead has numbered points.
2. Tap "Comment…" under point 2: the box opens and the keyboard comes up straight away.
3. Type a few words, then tap "Comment…" again: the box closes.
4. Tap it once more: the box opens with your words still in it.
5. Do the same on a computer: the cursor blinks in the box without a click on it.

I couldn't try it on an iPhone from here. A test opens the page in Chromium, clicks "Comment…" and checks the cursor is in that point's box; whether Safari raises the keyboard is the one thing only your phone can tell.

### 3. Left for later
Nothing from this card.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-07: planted by you; planned with one developer ticket.
- 2026-10-16, 03:26: f23-01 built by the local developer and merged at its first attempt, in 56 minutes, about 1.0 million local tokens and no Claude help ([session report](../sessions/2026-10-16-0326.md)). The checkpoint read it and found one harmless leftover line in the test.
- 2026-10-16: this review, round 1. One small test fix by the review, no ticket.
- Lessons:
  - The plan named the iPhone trap (focusing on the `toggle` event raises no keyboard) and told the developer how to avoid it; the developer did exactly that. Writing the phone-specific "why" into the ticket paid off.
  - The test checked "a comment box has focus", not "this point's box". The ticket's Done when said "that point's", and nothing held the developer to the difference. Fixed here.
  - Nine days from note to merge for 14 lines, nearly all of it waiting in the queue.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Small one-file tickets still wait days for their turn (F22 waited six, this one nine). The "small tickets first" idea from F22's review is still worth planting if you haven't.
  - A browser test that checks focus should name the exact element; I'll write that into ticket craft when the next focus ticket comes up rather than add a gate for it.

### 7. What clogged the factory line
- **Nine days between your note and the merge** (2026-10-07 to 2026-10-16), none of it in the work: the ticket waited its turn behind longer ones. What unclogs it: small tickets first (above).
- **56 minutes for 14 lines of script and 26 of test**, mostly the developer re-reading the 2,400-line test file at each step (62k tokens a step). Free in dollars, but it holds the GPU. What unclogs it: splitting `tests/factory_dashboard/test_planning.py` by page when it is next touched heavily.
- I can't read hours from the metrics database in a headless review; the figures are from the session report.

## What was built
- **The page** (`factory_dashboard/templates/thread.html`): each point's `<details>` gets the class `comment-box`. One click listener on the document catches a click on its summary, stops the browser's own toggle, flips `open` itself and, when it opened, focuses that point's `textarea.comment` in the same tap. Listening on the document means a conversation reloaded by `htmx.ajax` after Send still works. A keyboard Enter or Space on the summary fires the same click, so it works from a keyboard too.
- **Test** (`tests/factory_dashboard/test_planning.py`), by the developer, new: in Chromium, clicking point 1's "Comment…" opens the box with the focus in it; clicking again closes it and keeps the typed text. Without the change the focus stays on the summary, so the test fails as it should.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | nit | claude | The test checked that *a* `textarea.comment` had focus, not point 1's, and kept an unused `focused` line with an `is not None` check that proves nothing | Fixed in the review: one assertion that the focused element matches `li[data-point="1"] textarea.comment` |

Checkpoint finding C970-1 (the unused `focused` line): confirmed, folded into F1.

Read and found sound, no finding:
- **No double toggle.** `preventDefault()` on the summary's click stops the native toggle, so flipping `open` by hand doesn't cancel itself.
- **Only the thread's boxes.** The selector is scoped to `#conversation details.comment-box > summary`; the "Remove seed" `<details>` and the proposal page are untouched.
- **The "Send back" button** still turns on as you type: it listens to input on the textarea, which this doesn't change; its test passes.

Edited existing tests: none; the developer only added one. French: nothing to check, no user-facing string and no `coucou/locale/` file changed. Screenshots: no browser to look through in this job. After the fix, `uv run pytest -q tests/runner tests/factory_dashboard` gave 2303 passed, and ruff is clean on the edited file.

Score: 9/10. The smallest change that does it, at the first attempt, the way the plan asked. A point off for a test that stopped one step short of its own Done when.

Stop reason: none; nothing is left for a round 2.

## Factory
- **The flow:** one developer ticket, merged at the first attempt; one checkpoint, one nit. No stop, park, limit, direction or escalation.
- **Models:** the local model (Qwen) for the ticket; Claude Sonnet for the checkpoint; Claude Opus for this review. See the numbers below.
- **What to change:** nothing new; small tickets first (sheet, item 6) is the one lever this card shows.

## Workflow observations
- The checkpoint caught the dead line but not that the assertion next to it was too loose; the two were the same three lines. A checkpoint reading a test should compare each assertion with the ticket's Done when, word for word.

<!-- runner report -->
<!-- /runner report -->
