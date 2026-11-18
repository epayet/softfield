# Review: F216, a shorter, consistent review page, with the decisions made along the way

- **Status:** reviewed, waiting for your sign-off.

## Sign-off sheet

### 1. What changed
- **A card's page, once its review is written, reads top to bottom:** what it's about (with "Done when, as of now"), what changed, before and after, how to test, the decisions made along the way, then Sign off and What next.
- **Everything else folds into one plate, "Behind it":** each fold says what's inside ("7: 5 fixed, 2 left as they are", "$8.17, of which the review $3.41"). Findings now list each one with what happened to it, and What it cost shows the dollars per job role, to scale.
- **"None." is gone:** "Needs your answer" shows straight under the head only when something waits for you, on old cards too, and the planning thread does the same.
- **Numbered steps, nested bullets, `code` and links now render,** on old reviews and new. The review rewrote the list part itself: it still broke steps wrapped onto two lines, which real sheets have. Matches the mock-up, except that "Decisions made along the way" has no count in its header.

### 2. How to test it yourself
1. On your phone, open the board and tap F187 (harvested). Check the order: What it's about, What changed, How to test, What next, then Behind it with eight closed folds, each with a short line beside its name.
2. Open "What the review caught" and "What it cost": seven findings, each with fixed or left; the dollar rows with a grey bar each, the review's bar the longest.
3. Open M12 in coaster-ranker. Under How to test, the steps should count up without restarting at 1, with step 2's second line as part of step 2, not a new paragraph.
4. Open this card's page (F216) once this review is stored: "Decisions made along the way" sits between How to test and Sign off, and there is no "Needs your answer".

### 3. Done when, as of now
- **Your check:** this review is the first written to the new sheet: its page should show "Decisions made along the way" (step 4 above).
- **Met:** "Needs your answer" shows only when something waits; a sheet starting "None" shows no plate, on the page and on the thread.
- **Met:** Sign off comes after the reading part, What next after it.
- **Met:** the parts after What next are folds in one plate, each with its gist; an empty part doesn't show.
- **Met:** What the review caught lists findings with their outcome; What it cost gives the review's dollars beside the card's total.
- **Met:** numbered steps, nested bullets, backticks and links render, after the review's fix to wrapped steps and bullets under steps.
- **Met:** the review's prompt asks for the sheet and the runner's numbers only; this report is the first written that way.

### 5. Decisions made along the way
- **Lists render at any depth, and an indented plain line joins the item above it.** Real How to test sheets (M11, M12, M2) wrap steps onto indented lines, and the card's one-level rule left them broken. The other option was a fourth developer ticket, after three on the same function. *The review.*
- **`*Who.*` renders in italics.** The new "along the way" bullets end with who chose, in single stars, which showed raw before. *The lead on f216-03.*
- **The prompt no longer asks the review to name the pages it opened and the record it compared.** That line lived in the findings section, which this card removed. *The lead on f216-01.* A quoted fix is under What next.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** keep the proof that a review read the real page, now that the report has no findings section:
  > Let the review's JSON carry the pages it opened and the record it compared (ADR 37), and show them in the card's "What the review caught" fold, since runner/prompts.py lost that line when F216 removed the findings section.
- **Factory:** hand text parsers to the lead, not the local model: `_to_html` took four developer tickets and about 9 hours of the GPU and still broke on real sheets.
  > When a ticket asks for a parser or state machine (like _to_html), plan it for the lead, or give the developer a worked implementation to follow, since F216's developers spent 9 hours on one.

### 8. How the work went
- **Checkpoints found the list bugs one at a time.** Each fix ticket asserted the shape the last finding named, so the next shape broke. Tests built from a real stored sheet (M12's) would have caught all of them at once; the review's tests now do.
- **The lead's two tickets were quick:** the sheet's shape in 7 minutes on Sonnet, the page in 21 on Opus, matching the mock-up on the first try.

### 9. What clogged the factory line
- `_to_html`: about 9 hours of the local model over four tickets (17 November, 14:40 to 23:47), with two 75-minute timeouts, and the result still needed the review's rewrite. Fix: the planning rule quoted under What next.

<!-- runner report -->
<!-- runner report -->
