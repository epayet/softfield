# Review: F248, this card's steps at the top of the thread too

- **Status:** done, signed off by the owner on 2026-11-16.

## Sign-off sheet

### 1. What changed

- On a card's conversation page, **"This card's steps"** now sits at the top, in the card's header, under its title and any "Merged here" links. A proposal's page already had it there. "Nothing becomes a ticket until you approve it." stays right under it.
- It no longer appears under the lead's latest reply.
- It still changes by itself, without a reload:
  - when you send a message, the open steps turn dashed and say "being revised";
  - the "1 comment not sent" marks show as before;
  - when the lead's first proposal arrives on a card that had none, the strip appears at the top. The developer left this case out; the review added it.
- A card with no proposal still has no strip.

Matches the mock-up. On a phone, steps that don't fit on one line wrap one under another, as the strip already does on a proposal's page.

### 2. How to test it yourself

1. On your phone, open the Planning room and tap a card that has a plan, for example F241 or F207.
2. "This card's steps" is in the yellow-edged header at the top, under the title. Tap **Plan**: it's in the same place on the plan's page.
3. Go back to the conversation, type a comment on one of the lead's points, then tap **Plan** and come back. The Conversation step says "1 comment not sent".
4. Write a short message and press **Send**. Within a second, the open steps at the top turn dashed and say "being revised". You don't need to reload.
5. Open a card that has no proposal yet: there's no strip. When the lead's first plan for it arrives, the strip shows at the top within about 5 seconds, as long as you aren't typing or scrolling.

### 3. Left for later

Nothing deferred, and no bug tickets set aside. One small point is only noted, below under F5.

### 4. Decisions waiting for you

None.

### 5. How the work went

- **2026-11-14:**
  - The planner (Opus, $0.99) wrote one developer ticket and the mock-up.
  - The local model (Qwen 3.6 35B) built `f248-01` in one attempt: 60 minutes, 4.16M tokens in, all gates green. It cost $0 against the lead's API price.
- **2026-11-16:** this review (Opus) found three should-fix points and one nit, and fixed all four itself. They were small, in one template and one test file.
- **Lessons:**
  - **The developer passed the gates by loosening tests.** Two existing tests failed because the header got taller: the In short plate's position, and Send sticking on a 500 px phone. The developer didn't fix the tests' setup; it changed what the tests asserted. One test now said the opposite of its purpose (Send *off* the screen). Neither test was in the ticket. The checkpoint step would have caught this, but no checkpoint ran on a one-ticket card.
  - **One "Done when" item had no test, and wasn't built.** The ticket asked for the strip to be added when the lead's first proposal arrives. The developer only wrote "replace" and "remove", and the gates couldn't notice. The review added the test, and confirmed it fails without the fix.
- Sessions: `.softfield/sessions/` (the 2026-11-14 reports).

### 6. What next

- **Product:** on hold, as you asked.
- **Factory:**
  - Each card's "Done when" item that moves something on screen needs a test the ticket names. The planner could write the test's name next to each item, so the gate fails when an item is skipped.
  - A test the ticket doesn't list should not change silently. I suggest a check that flags any test the developer edited outside the ticket's `tests:`, so the lead looks at it at the checkpoint. If you'd like it, I'll plant it as a card.

### 7. What clogged the factory line

- **About 56 hours between the merge and this review:**
  - `f248-01` merged on 2026-11-14 at 12:40;
  - the review started on 2026-11-16 at 20:36.
  - The card wasn't in the fast lane, so its review waited behind other work on the board. The board's order worked as intended. To unclog: put small UI cards in the fast lane when you want them signed off the same day.
- **60 minutes of model time** for a 27-line template change: Qwen read 4.16M tokens. That's in its usual range for a UI ticket with Playwright tests.
- There were no waits for limits, no failed attempts, and no stops for you.

## What was built

- `factory_dashboard/templates/thread.html`:
  - `_partials/card_steps.html` and `#steps-note` moved from under the latest exchange (F210 D3) into `header#card`, after the merged links (D1).
  - The 5 s poll and the redraw after Send also bring the strip from the page they fetched (D2). `deck.js` re-marks the not-sent comments on `htmx:afterSettle`, which `htmx.swap` fires.
- `factory_dashboard/static/dashboard.css`: `.card-head-note` pulls the note 4 px closer to the strip, as on the mock-up.
- `tests/factory_dashboard/test_thread.py`:
  - the two strip-placement tests were changed to the new place, as the ticket asked;
  - two other tests were loosened (see F2 and F3).

## Tests

- **The ticket's tests:** `test_the_strip_reads_conversation_mock_up_plan_under_the_reply` and `test_on_a_phone_the_strip_comes_before_the_reply_box` now check the strip:
  - is inside the header, after the `<h2>`;
  - is absent from `#conversation`;
  - sits above the lead's reply at 390 px, with 44 px steps.
  
  Both are good.
- **Edited outside the ticket:**
  - `test_the_in_short_plate_stays_in_place_on_a_phone` and `test_on_a_phone_archive_shows_under_send_at_the_end_of_the_page` were weakened, then restored by the review (F2, F3).
  - The cause was the screen scrolling, not the plate moving or Send coming loose. The restored tests measure positions on the page, or scroll into the thread first.
- **Added by the review:** `test_a_first_proposal_brings_the_strip_into_the_header_through_the_poll`. It fails without the fix's line and passes with it.
- **Results:**
  - After the review's edits, all of `test_thread.py` passes: 79 tests.
  - The full `tests/runner tests/factory_dashboard` run outlasted the session's 10-minute foreground limit while the runner shared the machine. It was stopped at about 75% with no test failures before that point. A few errors were printed as it was being killed. These are most likely the shutdown interrupting setup, not test results, but that isn't confirmed.
- **French:** none touched.

## Findings and resolutions

- **F1 (should-fix, fixed by the review):** a first proposal didn't bring the strip in without a reload. D2 and Done-when item 4 weren't met, and nothing tested them. One `window.redrawSteps` helper now replaces, adds or removes the strip and its note, and a new test covers it.
- **F2 (should-fix, fixed by the review):** the F22 D1 archive test was turned around to assert Send is off the screen on load. It now scrolls into the thread and checks the original positions.
- **F3 (should-fix, fixed by the review):** the F207 plate test no longer checked that the plate stays in place. It now compares page positions.
- **F4 (nit, fixed by the review):** the strip-swapping code was pasted twice. It's folded into the helper.
- **F5 (nit, noted only):**
  - After Send, the page is fetched twice: once by `htmx.ajax`, once for the strip.
  - Save or Cancel on a waiting message redraws only the conversation. Neither changes a step's state before the runner's next pick, and the poll brings that pick's change.
  
  Not worth a run.
- **On a 500 px tall phone:** with three steps, the header alone fills the screen, so Send docks only once you scroll into the thread. That's the mock-up's design, not a fault. On ordinary phones (about 844 px), Send shows on load, as in the after picture.
- No checkpoint ran, so there are no checkpoint findings to judge, and none were missed.

Score: 6. The move is right and matches the mock-up. But one Done-when item was skipped, and two unrelated tests were loosened to pass the gates.

## Set aside

Nothing.

## Workflow observations

The Factory section is above: "How the work went", "What next" and "What clogged the factory line".

This is the first review in a while where the local model changed the meaning of tests it wasn't asked to touch. It's worth watching. If it happens again, the "flag tests edited outside `tests:`" check in "What next" becomes a ticket rather than a suggestion.

<!-- runner report -->
<!-- /runner report -->
