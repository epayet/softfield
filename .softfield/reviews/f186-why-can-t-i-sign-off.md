# Review: F186, a sign-off stays signed

- **Status:** review done, waiting for sign-off.

## Sign-off sheet

### 1. What changed
- **F142's sign-off has left your desk,** with no press from you. The runner cleared it on 2026-11-04 at 02:07, and F142 now says done.
- **A sign-off now stays signed.** If you sign a card off while its review is still running, the end of the review no longer brings the sign-off back or marks the card as in review again.
- **Pressing Sign off on a card already signed off just settles it.** It used to fail with "tag already exists", which is what happened to your six presses on F142 after the first.

### 2. How to test it yourself
1. Open the Overview: it doesn't ask for F142's sign-off.
2. Open F142's card: it says done.
3. Next time a card's review is running and its sign-off is offered, sign it off. When the review ends, the card should stay done and not come back to your desk. This can't be set up on demand, so check it when it happens.

### 3. Left for later
- F142's end date stays 2026-11-04 instead of 2026-10-28, so the reports count it in this week. It only affects that one card's date, so I'd leave it.
- A review that stops for you (an ADR needed, a security point) on a card you signed off during that review puts nothing on your desk. It's rare; "What next" has the fix.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-29: planned from your note in the Planning room, and you approved the plan the same morning.
- 2026-11-04 01:57 ([session](../sessions/2026-11-04-0157.md)): `f186-01-sign-off-stays-signed`, the lead's ticket (protected `runner/`), Sonnet, first attempt, 6 minutes, $0.33.
- 2026-11-04 04:53 ([session](../sessions/2026-11-04-0453.md)): review round 1 found one blocking gap and fixed four findings itself, all in protected code.
- 2026-11-04 05:39: review round 2 confirmed those four fixes and caught a mistake in one of them (F6), fixed in the same round.
- Lessons:
  - **A review's own fix needs the same doubt as a ticket's.** Round 1's end-date fix assumed the first sign-off had always reached the database. If it hadn't, the card would have ended with no date and dropped out of the reports. Round 2 found this by asking what each new branch does when the earlier step failed.
  - **The ticket's main test stopped one step short of the bug.** It replaced the review with a stand-in, and the review itself was what set the card back to "in review". The new test runs the real review loop, with a sign-off in the middle of it.
  - **The fix went in the one place the ticket named.** The card's own account of F142 named `_record_review`, but the check went only where the verdict is recorded. For a race like this one, every write after the sign-off needs the check, so I went through them all.
  - **The heal could only cover part of it:** it starts from open items, so a card wrongly back "in review" with no open item would never have been noticed.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** stop a review's rounds as soon as its card is signed off. Today the review goes on to its next round and spends Claude on work you've already accepted. It's a small change in the review loop, and it would also remove the case in "Left for later". I'd plant it as a card of its own.
- **Factory:** when a press of yours fails, say so on the desk and put the fix first. F142's failures went into the requests' results while the same button stayed on your desk, and F186 then waited over five days for its turn on the board.

### 7. What clogged the factory line
- **F142's item stayed open for 6 days 17 hours** (2026-10-28 09:00 to 2026-11-04 02:07), with six failed presses. Almost all of that is the wait below.
- **F186 waited 5 days 15 hours for its turn** (plan approved 2026-10-29 10:42, ticket started 2026-11-04 01:57), for 6 minutes of work. That is the board's order working, but the card was a fault in your own sign-off button. To unclog it, put such a card at the top of the board when it's planned.
- **The review waited 2 hours 46 minutes** (queued 02:07, started 04:53), parked until 04:10 with Claude's 5-hour window over its cap, then started about 43 minutes later. The cap did its job, so there's nothing to change.

## What was built
- `runner/cli.py`: `_review` records no verdict for a milestone already signed off (D1).
- `runner/owner.py`: `signoff` on a milestone already signed off settles it, with no file written, no commit and no tag (D2). `heal_signed_off` resolves open `signoff` and `review-stop` items of signed-off milestones and sets them done (D3).
- `runner/requests.py`: `apply_requests` runs the heal before each pick.
- Added by this review:
  - `runner/milestone.py`: the review loop doesn't set a signed-off milestone back to `review` or replace its signed sheet.
  - `runner/cli.py`: `softfield milestone` makes the same check as `_review`.
  - `runner/owner.py`: settling keeps the end date and keeps a score given. A sign-off the database missed gets its end date when it is settled.

The heal worked on real data before this review: item 250 was resolved at 02:07:11, and F142's milestone is `done`.

No existing test was edited: the ticket and this review only add tests. No French changed.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | A review ending after the sign-off still set the milestone back to `review`, before D1's check ran, and the heal couldn't see it | Fixed in `review_milestone` and `_record_review`; new test runs the real loop |
| F2 | should-fix | claude | `softfield milestone` still recorded a verdict after a sign-off | Fixed, with a test |
| F3 | should-fix | claude | Settling moved the milestone's end date | Fixed for the future, with a test; F142's row keeps 2026-11-04 |
| F4 | nit | claude | A second sign-off dropped the owner's score | Fixed, with a test |
| F5 | nit | report | A review stop needing the owner, on a card signed off during that review, raises nothing on the desk | Not fixed: rare. Stopping the rounds at the sign-off (What next) removes the case |
| F6 | should-fix | claude | F3's fix left a card with no end date when its first sign-off never reached the database, so settling marked it done without a date | Fixed in round 2: the first write that finds no end date sets it; new test |

Round 2 re-read the fixes for F1 to F4: F1, F2 and F4 hold as written, and F3 holds with F6's change. F1's test runs the real loop, and F2's and F3's tests check what they claim.

Checkpoints: none read this ticket, so there's nothing to judge and no "missed".

## What was set aside
- F142's end date (F3): correcting it would be a one-off write to the database, for one card's place in one week's report. I'd leave it.
- F5, as above.
- F142's card and review say signed off on 2026-11-02, not 2026-10-28, because each failed press rewrote the date before the tag failed. This no longer happens, and I'd leave the old text.

## Workflow observations
- A lead ticket on Sonnet at $0.33 did most of the card, but missed the part that needed tracing the whole path. The ticket's Context did name `_record_review` and its Done when did ask for the status to stay; the test just didn't reach it. A Done when about what a real path does should have a test through that path.
- Fixing in the review was right here: all four fixes were small and in protected code, which a developer can't take. F142's review showed the cost of routing such a fix out: four days for ten lines.
- Round 2 earned its cost: nothing else reads a fix the review makes itself, and F6 would otherwise have reached main. Its effect would have been quiet: nothing fails, and a card just goes missing from the reports. No change to the loop is needed.

<!-- runner report -->
<!-- /runner report -->
