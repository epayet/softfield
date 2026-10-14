# Milestone F42: The space for me to scroll on a planning proposal card is very small

> **State:** ready · **Priority:** 2 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
For example f17. Lots of sticky stuff meaning scrolling window small

### From F64: 'your review' in planning doesn't have to be sticky,… (merged by the lead on 2026-10-08)
'your review' in planning doesn't have to be sticky, scrolling to see is fine there'll be more screen space this way

## What squeezes it (read from the code, 2026-10-08)
On a phone (390 × 844, about 660 px left under the browser's own bars), the review page `factory_dashboard/templates/proposal.html` stacks:
- the top bar, sticky at the top: brand, status and Pause, the hazard stripe, the tabs: about 130 px;
- the dock "Your review", sticky at the bottom: its title, the count, the button and a sentence: about 175 px;
- between them about 350 px, where F17's mock-up sits in a box 480 px tall that scrolls on its own: a scroll inside a scroll, never seen whole. In that box the mock-up's scripts don't run either (the iframe's `sandbox`), so F17's "tap the dot for its words" can't be tried.

## Outcome
- **The mock-up opens full screen.** "Open the mock-up" opens it as its own page, at the screen's real width, with its scripts on (its own sandbox CSP already keeps it from posting anything). On a phone that link replaces the box; on a wide screen the box stays, as tall as the screen allows, with the same link.
- **The dock is one row on a phone:** the count and the button side by side, about 60 px. Its title and its standing sentence go (the page already says "the rest counts as agreed"); the sentence after a send still shows.
- **The top bar steps aside while reading:** on a phone it slides away when the owner scrolls down and comes back as soon as they scroll up, or at the top of the page. Wide screens keep it as today.
- Together: about 560 px of a phone's screen for the points instead of about 350.

## Not here
- The thread page's own dock (the message box): same pattern, but it holds a text field; look at it after this, with F41 (the raw text above the points).
- F17's ticket already takes one row off the top bar (the dot and the sign beside the brand); f42-02 builds on it.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | review-page-room | D | 3 | – | the mock-up full screen (a link on a phone, a taller box with the link on a display); the dock one row on a phone |
| 02 | top-bar-steps-aside | D | 3 | f17-01, f42-01 | on a phone the top bar hides while scrolling down and returns on scrolling up |
