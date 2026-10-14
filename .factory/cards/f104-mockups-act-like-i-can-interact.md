# Milestone F104: Mockups act like I can interact with but I can't, f54 is…

> **State:** done · **Priority:** 2 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-13. Base: git tag `f104-mockups-act-like-i-can-interact-start`. Report: [`.factory/reviews/f104-mockups-act-like-i-can-interact.md`](../reviews/f104-mockups-act-like-i-can-interact.md).
> Planted by the owner on 2026-10-10.

## Notes
Mockups act like I can interact with but I can't, f54 is blocked because of that

## Why it happens (from the code, 2026-10-10)
- The review page shows a mock-up in a frame, `<iframe id="mockup" … sandbox>` in `factory_dashboard/templates/proposal.html`. A bare `sandbox` turns the page's scripts off.
- Every mock-up's buttons are script: F54's `f54-mockup/moves.html` draws its whole queue, its five option tabs and its "Refresh", "Reload" and "Runner's next pick" buttons that way. In the frame the tabs show, pressing them does nothing, and the queue is empty.
- The mock-up's own address already lets scripts run: `mockup_file` in `factory_dashboard/planning.py` answers with `Content-Security-Policy: sandbox allow-scripts`. Only the frame is stricter than f6-08 meant.
- F42 found the same thing on 2026-10-08 ("In that box the mock-up's scripts don't run either") and its ticket f42-01 adds an "Open the mock-up" link, which on a phone replaces the frame. It is queued, not built. On a wide screen it keeps the frame, still with its scripts off.

## Outcome
- A mock-up works where the owner reads it: in the review page's frame on a wide screen its buttons, tabs and switches answer, as they do on its own page.
- With f42-01, on a phone the mock-up opens full screen from its link, working too.
- Nothing a mock-up runs can act as the dashboard: no request, no reading of the page around it.

## Decisions
- **D1 The frame lets scripts run, and nothing else:** `sandbox="allow-scripts"`, the same words as the route's CSP. Never `allow-same-origin` (with it a mock-up's script would be the dashboard: it could press Approve), nor `allow-forms`, `allow-popups` or `allow-top-navigation`. The mock-up stays in an origin of its own, so its posts carry `Origin: null`, which `/requests` already refuses (`tests/factory_dashboard/test_requests.py`).
- **D2 Checked in a real browser:** the test runs a mock-up with a script inside the review page in Chromium, since only the browser says what a sandbox allows (lead.md, F12's lesson).
- **D3 After f42-01:** both change the same lines of `proposal.html`, so f104-01 waits for it. F42 keeps the link, the frame's height and the phone; F104 only makes the frame work.

## Tickets
| # | id | who | diff | depends | what |
|---|----|-----|------|---------|------|
| 01 | f104-01-mockup-frame-runs-scripts | lead | 2 | – | D1 and D2. Done by the lead with the owner, 2026-10-13 (`eda0843`), before f42-01 and not after it (D3): the owner was blocked on F54's mock-up |

## Done when
- On a wide screen, open F54's mock-up proposal: press "A · stays in place", then ↑ on a row; the tab changes and the row answers, inside the review page.
- On a phone (after f42-01), "Open the mock-up" opens it full screen and it answers the same way.
