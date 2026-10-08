# Milestone F28: the first time i clicked on the pause button nothing happened, but then eventually it worked

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Notes
(none)

### From F29: the top was saying "resuming" but in the overview page the resume button was still available (merged by the owner on 2026-10-08)
(none)

## Outcome
- Pause or Resume, in the top bar, shows what was asked at once and keeps showing it until the runner's own state agrees: the 5 s refresh no longer puts the old words and the old button back.
- A request that doesn't reach the dashboard's server says so, and the button comes back to try again.
- Overview's Now says the same as the top bar, "Resuming…" included (F29), and the top bar is the one Pause/Resume button.

## Why it happened (from the code)
- Every page polls `/live` every 5 s and redraws `#factory-status` (`factory_dashboard/templates/_partials/bar_status.html`). A click sets "Pausing after this job" and removes the button (`base.html`'s script), but a poll that started before the request was stored brings back "Running" and Pause: the click looks lost, and the next poll shows the pause. The request can also wait up to 10 s on the database while the runner writes (`writable` in `factory_dashboard/app.py`), so one or two polls can land first.
- The browser test for the button (`test_pause_in_the_top_bar_shows_pausing_at_once_and_posts_a_pause`) blocks `/live`, so it never met the race.
- Now on Overview (`factory_dashboard/templates/_partials/running.html`) has its own Pause/Resume with the same race, and no "Resuming…" state: the top bar said "Resuming…" while Now still offered Resume (F29).

## Decisions
- **D1 Hold the asked state through polls:** after a click, an incoming top bar whose button still posts the kind just asked is not swapped in (htmx 2's `htmx:oobBeforeSwap`); the first bar whose button differs (the server has the request) is. No server change.
- **D2 Say when it failed:** if the post fails (an error answer or no answer), the bar shows "Didn't reach the factory: try again" and the poll's bar is swapped in again.
- **D3 One button:** Now drops its Pause/Resume and keeps only the state line, with "Resuming…" added; the top bar, on every page since f6-16, is the control. F17 restyles that one button later.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | pause-survives-the-refresh | D | 4 | – | D1, D2 |
| 02 | now-shows-resuming-without-a-button | D | 2 | – | D3 (F29) |

## Done when
- On a phone, press Pause while a job runs: "Pausing after this job" shows at once and stays, never flicking back to Pause; then Resume: "Resuming…" stays until the runner resumes.
- Overview's Now says the same as the top bar at every step, and has no button of its own.
