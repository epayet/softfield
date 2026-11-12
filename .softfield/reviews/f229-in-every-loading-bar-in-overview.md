# Review: F229, one bar instead of two

## Sign-off sheet

### 1. What changed
Every bar on the dashboard is now a single bar. The pale strip with four chunks under it is gone from:
- the Overview's Agent allowance (Claude's 5-hour window and week, and Copilot's month),
- the planning room's "The lead's window" (both bars),
- each card's ticket count on the board.

The words under each bar keep a small gap from it, so they don't touch the bar or the mark that sticks out above and below it. On the board, the bar's spacing is unchanged. The fill, the colours, the 75% mark and the pace tick all look the same as before.

Matches the mock-up.

### 2. How to test it yourself
1. On the phone, open the Overview and scroll to Agent allowance. Each bar should be one bar with no strip under it, and "resets at …" should sit just below it without touching.
2. Open Planning. "The lead's window" should show two single bars, each with its line of text under it.
3. Open the Board. A card with tickets should show its bar and then "N of M tickets", with nothing in between.
4. Switch to the light theme and check one of these again. The mark should still stand out.

### 3. Left for later
Nothing set aside. One small note on a test's message, not worth a run (see Findings).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-05: Claude (Opus) planned the card and drew the mock-up in 2 minutes ($0.98).
- 2026-11-06: the local model (Qwen) did the one ticket on its first attempt in 32 minutes (18 minutes of model time, 14 minutes of checks). Nothing was escalated.
- 2026-11-12: Claude reviewed it and found nothing to fix.
- Lessons:
  - A small ticket with exact steps in Context (which elements to remove, which margins to add, which test to replace) came back right the first time. That is the shape that works for the local model.
  - The ticket replaced the old test with one that reads every template and the stylesheet, so the strip can't come back. That matters because f219's mock-up still draws the strip.
- Logs: `.softfield/sessions/2026-11-06-0111.md`.

### 6. What next
- **Product:** product work is still on hold, as you asked.
- **Factory:** about 1.4M tokens in for a 9-line change is a lot. The session report shows 9 edits in a row without running anything. That cost only local time, and the result was right, so nothing changes yet. If it shows up on bigger tickets, the developer's instructions should ask for a test run after every few edits.

### 7. What clogged the factory line
From the `jobs` table:
- **Waiting for its turn: about 1¼ days** from the plan (11-05 11:34) to the developer (11-06 18:33), then **about 5½ days** until this review (11-06 19:05 to 11-12 04:28). Both waits were queue order, with other work ahead of it. No agent sat idle because of them.
- No failed attempts, no limits hit and no stops for you.

<!-- runner report -->
<!-- /runner report -->

## What was built
`f229-01-no-strip-under-meters` (commit 86e13ea91):
- **Templates:** the `meter-ticks` element is removed from `_partials/allowance.html`, `planning.html` (both places) and `board.html`.
- **Stylesheet:** the `.meter-ticks` rule and its comment are gone. `.meter` gets `margin-bottom: 6px` and `.card .meter` gets `margin-bottom: 0`, as D2 asked. The other bars (`allowance_bar.html`, the job page's context bar) pick up the 6 px gap too. That's harmless: on the job page the bar is the last thing in its cell.
- **Tests:** `test_gauge_has_quarter_ticks`, which asserted the strip, is replaced by `test_no_template_or_stylesheet_names_meter_ticks`. The new test reads every template under `factory_dashboard/templates/` and `dashboard.css`. This is the one existing test the developer changed, and the change was what the ticket asked for. The test fails on the old code. The mock-up still contains `meter-ticks`, but it lives under `.softfield/cards/`, outside the folders the test reads, as intended.

There's no French in this milestone.

## Findings
| Id | Grade | Route | What |
|---|---|---|---|
| F1 | nit | report | The new test's failure message names a template by its file name (`allowance.html`), not its path (`_partials/allowance.html`). Template names are unique today, so it still points to the right file. |

**No checkpoint findings.** No checkpoint ran on this milestone.

Score: 9/10.

## Factory
- **Flow:** one ticket, passed on its first attempt, no stops, no limits, no parks.
- **Models:** the Opus plan cost $0.98. The local model got everything right from a precise ticket, and the gates and pictures agree.
- **To change:** nothing.
