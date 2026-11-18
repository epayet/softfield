# Review: F266, the over-pace stripe covers the week meter's green fill to its end

- **Status:** done, signed off by the owner on 2026-11-18.

## Sign-off sheet

### 1. What changed
When the week is over pace, the hazard stripe on the Claude week meter now ends exactly where the green fill ends: the tiny green dot (a 1–4px sliver) to the right of the stripe is gone, on the overview and in the Planning room. The yellow pace post sits where it did; nothing else on the meters moves.

No mock-up for this card (it restores the look the meter already meant).

### 2. How to test it yourself
1. On a day the week is over pace (the "Over pace" plate shows under the Claude week bar), open the dashboard overview on your phone.
2. Zoom in on the right end of the Claude week bar: the stripes run to the very end of the green, with no green pixel past them.
3. Open `/planning` and check the same on its week bar.
4. On a day under pace, the bar shows the green fill and the dashed post only, as before.

### 3. Left for later
Nothing from this card.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-18 12:19 ([session](../sessions/2026-11-18-1219.md)): 1 ticket, merged by the local model on its second attempt; no escalation. The local model read 1.8M tokens; Claude's share was the planning and this review.
- Lessons:
  1. Attempt 1 spent its 20 minutes on 17 reads and greps (about 70 s a step) without an edit, and was stopped; the "one small edit at a time" nudge got attempt 2 there in 39 minutes. A six-line template change took an hour of GPU, but no Claude time.
  2. The developer did what the ticket said for the stripe, but kept the fill and the post formatting their own numbers, so "rounded once each" held only by coincidence. The review made all three reuse the same two numbers.
  3. The dashboard and runner tests took over ten minutes in this review, which is longer than a single check here can wait.

### 6. What next
- **Product:** product work is on hold; nothing to suggest.
- **Factory:**
  - The test suite is now the slow part of every check and every review; it's worth finding the slowest tests and speeding them up.
    > The dashboard and runner tests (`tests/runner`, `tests/factory_dashboard`) take over ten minutes in a review; list the slowest with `pytest --durations=30` and speed up or share the fixtures behind the worst of them so the suite runs in a few minutes.

### 7. What clogged the factory line
- **A stopped attempt, 20 min** (12:38–12:58): the local model read and grepped for 20 minutes without editing. Unclog: nothing new; the stop rule and its nudge worked as meant, and attempt 2 passed.
- **The passing attempt, 39 min** (12:58–13:37) for a six-line change: about 70 s a step over 34 steps. Unclog: a faster test suite (above) shortens each of the developer's test runs.
- No waits for limits, no stops for the owner, no tickets waiting on each other.

## What was built
`f266-01-stripe-covers-the-fill-to-its-end`: in `factory_dashboard/templates/_partials/allowance_bar.html`, the over-pace stripe now starts at `calc(<post>% + 1px)` (matching the fill's 1px inset) and is `<fill>% - <post>%` wide, from the same rounded percents as the fill and the post (card D1). The two existing over-pace tests expect the new style, and a new test (`test_pace_rounding_discrepancy_stripe_width_equals_fill_minus_post`) picks 35.5% used against a 33.3% post, where rounding `used - post` alone gave 2% and the fill minus the post is 3%. It fails on the old template.

## Findings and resolutions
- **F1 (nit, fixed by the lead):** the fill span and the post span still formatted their own `'%.0f'` percents, so the stripe and they matched only because `round | int` and `'%.0f'` happen to agree; the new lines were also indented one space off the macro's, and the new test's docstring quoted numbers it doesn't use. Now `rfill` and `rpost` are computed once and used by the fill, the stripe and the post, the indentation matches, and the docstring states the case it tests. The rendered HTML is unchanged, so the tests are too. Checked: the only tests that render this macro are in `test_overview.py` and `test_planning.py`, and those 338 pass. The full `tests/runner tests/factory_dashboard` run was stopped at 59% after more than ten minutes with no failures; the runner's gates run it in full.

Edited tests checked: both existing over-pace tests only change the expected stripe style, from `left:33%` to `left:calc(33% + 1px)`; the widths (32%) are unchanged and right. No French in this card.

## Set aside
Nothing.

## Workflow observations
- The card and ticket gave the exact expected style strings, which is what got a slow local attempt to a correct result; worth keeping for small UI fixes.
- See lesson 3 and the Factory line in "What next" on test-suite time.

<!-- runner report -->
<!-- /runner report -->
