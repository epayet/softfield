# Review: F252, the Open button opens a new tab

- **Status:** done, signed off by the owner on 2026-11-17.

## Sign-off sheet

### 1. What changed
On the Projects page, a running app's "Open ↗ :port" button now opens the app in a new tab, so the dashboard stays where you left it. Logs, Run, Stop and the plant button still work in the page, as before.

No mock-up: nothing on screen looks different.

### 2. How to test it yourself
1. On the dashboard, go to Projects and start an app (Run) if none is running.
2. Press "Open ↗ :port" on its row. The app opens in a new tab, and the Projects page is still there in the first one.
3. Press Logs on the same row. The logs open in the same tab, as before.
4. Try steps 2–3 on your phone too. On a phone, the new tab opens as a separate tab in the browser.

### 3. Left for later
Nothing deferred and no bug tickets.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-16 19:35: Opus planned one ticket (38 s, $0.36).
- 2026-11-16 22:32–22:44: Qwen built `f252-01-open-in-a-new-tab` on its first attempt (12 min: 6.5 min model, 5.4 min gates; 79k tokens in). Session: [`.softfield/sessions/2026-11-16-2059.md`](../sessions/2026-11-16-2059.md).

Lessons:
- **A small, exact ticket passes first time.** The ticket named the line to change, the example to copy (`milestone.html`'s live link) and the existing test assertion to turn around. Qwen took 4 steps.

### 6. What next
- **Product:** product work is on hold (owner, 2026-10-04). Nothing to suggest.
- **Factory:** nothing new from this milestone. It shows what a well-sized developer ticket looks like.

### 7. What clogged the factory line
About 3 hours between the plan (19:35) and the build (22:32), of which 12 minutes were the work. The ticket waited in the queue behind the run's other cards (the run started at 20:59, F249 went first and stopped after 20 minutes without an edit, and F251 used the local model next). **What would unclog it:** nothing specific to this card. A one-line ticket waits behind larger ones because the board order decides, which is as the owner wants (2026-10-22).

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/templates/_partials/app_row.html`: the Open link gets `target="_blank" rel="noopener"`, like the other new-tab links (`milestone.html`, `proposal.html`). Its href and text are unchanged.
- `tests/factory_dashboard/test_projects.py`: `test_a_running_app_shows_running_stop_open_and_logs` now asserts the link's full opening tag with both attributes. The old `'target="_blank"' not in row` check is gone, because it stated F239's opposite choice. The Logs assertion (`href=…/logs">Logs</a>`) still proves that Logs has no `target`.

## Findings and resolutions
None. The diff is the change the plan asked for. The one existing test edit is the reversal the ticket asked for, and it fails without the change.

There were no checkpoint findings to judge. Score: 9/10. Exact, minimal and tested. It loses a point only because the test proves Logs stays in the page indirectly (through the tag's exact end) rather than with an explicit check.

The milestone's tests: `tests/factory_dashboard/test_projects.py`, 31 passed.

French: none touched (factory only).

## Set aside
Nothing.

## Stop reason
None. No findings, so the loop ends after this round.

## Factory
- **Flow:** one plan, one developer attempt, merged. No stops, no parks, and you didn't need to step in.
- **Models:** Opus planned it ($0.36). Qwen (local) built it on the first attempt. The lead reviewed it.
- **What to change:** nothing.
