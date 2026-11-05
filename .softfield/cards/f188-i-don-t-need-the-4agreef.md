# Milestone F188: Drop the 'N agreed · M to change' count from the review's phone bar

> **State:** done · **Priority:** 6 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-05. Base: git tag `f188-i-don-t-need-the-4agreef-start`. Report: [`.softfield/reviews/f188-i-don-t-need-the-4agreef.md`](../reviews/f188-i-don-t-need-the-4agreef.md).
> Planted by the owner on 2026-10-29.

## Notes
I don't need the '4agreef 0 to change ' to be sticky in the planning sticky approve plan bar it takes too much space

## Plan
Mock-up: [`f188-mockup/review-dock.html`](f188-mockup/review-dock.html).
- **D1 The count leaves the phone's bar:** at 639 px and under, `#review-count` is hidden by CSS; the bar holds the button and the closed Reject… fold. The yellow dots above and the button's "Send N changes back" already say how many points have a comment.
- **D2 What doesn't change:** the template and its script (the count stays in the page and keeps updating), the wide screen (the review sits in its side panel there, not stuck to the bottom), the bar staying in view on a phone (F42 kept it there).

| # | Ticket | Who | Difficulty | Waits for | What |
|---|---|---|---|---|---|
| 01 | count-leaves-the-phone-bar | developer | 1 | – | hide the count in the phone rules; the test checks it's gone |
