# Review: F254, the allowance takes less height on a phone

- **Status:** done, signed off by the owner on 2026-11-17.

## Sign-off sheet

### 1. What changed
On a phone, the Overview's Agent allowance is shorter. Each of the three windows (Claude's 5 hours, Claude's week, Copilot's month) is now a row with a thin line under it, not a box. The name, the reading and the meter sit beside the "use reserve" lever. The small words ("resets…", "read at…", "kept for you from here") run on as one line of text with "·" between them, and "at this rate" keeps its own line. Every word, colour and lever is still there, and the lever is still 44px tall so it's easy to tap. The wide screen looks as it did.

Matches the mock-up, except that the reading keeps today's words ("5-hour window: 48%") on the right where the mock-up put the window's name next to "Claude" and the percent alone in bold.

### 2. How to test it yourself
1. On your phone, open the Overview and scroll to Agent allowance.
2. Each window is a row with a thin line between it and the next, and no box around it.
3. In Claude's two rows, "Claude", its reading and the coloured bar are on the left, beside the "use reserve" lever. The three rows together are about a thumb's length, much less than before.
4. Under each bar, the small words follow one another on one or two lines with "·" between them. "at this rate…" starts on a new line.
5. On the computer, open the Overview: the allowance is three windows side by side, as before.

### 3. Left for later
Nothing deferred and no bug tickets. Two small points are only noted below (Findings).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-16 22:26: Opus planned one developer ticket and the mock-up (3 min, $1.17).
- 2026-11-16 23:24 to 2026-11-17 03:03: Qwen failed `f254-01-allowance-rows-on-a-phone` three times. Attempts 1 and 3 stopped with no edit after 20 minutes, the third under an Opus direction ($0.62). Attempt 2 (70 min) rewrote the template, left the name above the lever's band (361px for a 280px limit) and broke the wide screen's rules. Opus finished it on the branch in 19 minutes ($2.09). Session: [`.softfield/sessions/2026-11-16-2059.md`](../sessions/2026-11-16-2059.md).

Lessons:
- **A phone regroup is the lead's, or a CSS-only ticket on the template's own order.** F9 had already learned this, and the plan still sent it to the developer. The escalation added note 13 to `.softfield/developer.md`, with the worked example and its test.
- **Rewriting the template to change a phone layout moves the wide screen too.** The finish used one `display: contents` wrapper and kept everything else in the media query, and a wide-screen test now guards it.

### 6. What next
- **Product:** product work is on hold (owner, 2026-10-04). Nothing to suggest.
- **Factory:** the planner should send phone layout tickets (a regroup inside a media query) to the lead, or write them as "CSS only, template order kept" with the test's shape, as note 13 now shows. If the next one is still routed to Qwen and fails the same way, make it a pre-flight check rather than another note.

### 7. What clogged the factory line
About 4 h 40 min from the plan (22:26) to the merge (03:07), of which about 20 minutes were the work that merged:
- **About 1 h in the queue** (22:29 to 23:24), behind F249 and F251 on the local model. Nothing to unclog: the board order decides.
- **About 1 h 50 min of failed Qwen attempts** (20 + 70 + 20 min). **What would unclog it:** routing it to the lead at planning time (note 13 now says so for developers; the planner needs the same rule).
- **About 1 h 30 min waiting for the direction** (00:54 to 02:22): Claude's 5-hour window was over its cap, and F251's direction was parked the same way. **What would unclog it:** with the ticket routed to the lead, there's no direction to wait for.
- **About 40 min from merge to review** (03:03 to 03:43), behind the reviews of F249, F251 and F252.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/templates/_partials/allowance.html`: the name and the reading are wrapped in one `<span class="reading">`. That's the only template change.
- `factory_dashboard/static/dashboard.css`: `.allow .reading { display: contents }` outside the media query, so the wide screen's flex line sees the same three children as before. Inside `max-width: 639px`, each window is a two-column grid. Its first `.line` is `display: contents`, so the reading takes column 1, row 1, the meter takes column 1, row 2, and the lever takes column 2 across both rows. The small words become a block of text with `small + small::before { content: " · " }`, and `.rate` is a block with no "·". Window boxes are gone. Each window has padding and a 1px `--grid` rule, and the last one has no rule.
- `tests/factory_dashboard/test_overview.py`: six browser tests, one for each Done-when and decision line. They check the height ≤ 280px at 390px (the "Over pace" plate subtracted), no box and only a thin rule, the reading and the meter inside the lever's band, the run-on words with "·" and "at this rate" on its own line, the wide screen as before, and every word on screen with no overlap at both widths.
- `tests/factory_dashboard/test_line.py` (an existing test changed): `test_phone_rows_show_the_three_busiest_and_a_toggle_opens_the_rest` now scrolls to the top before its overlap check. The shorter panel put a lever under the sticky top bar after the toggle's scroll, which is not a real overlap. The assertion itself is unchanged.
- `.softfield/developer.md`: note 13.

The range `f254-…-start..main` also holds F249's review fix (`factory_dashboard/planning.py`, `tests/factory_dashboard/test_planning.py`) and the F249, F251 and F252 review reports. They were reviewed in their own milestones and aren't part of this one.

## Findings and resolutions
- **F1 (nit, report only):** the phone reading keeps today's words ("5-hour window: 48%") where the mock-up drew "Claude 5-hour window" with "48%" alone in bold. D1 allows a template change only for a wrapper and keeps the wide screen as drawn, so this is the right trade. The words and their order are the same, and only the emphasis differs.
- **F2 (nit, report only):** no phone test draws the Fast lane line or the "Last hours" plate, which D3 keeps. By the code, the Fast lane line becomes a row with a thin rule, like the windows (it used to share their box), and the plates span the window's whole grid. The 280px test does draw the "Over pace" plate. Not worth a run.

The tests were read against D1–D3. Each fails on main's rules (the 280px one at about 420px). The wide-screen test pins name, reading, lever, meter and words in the order main draws them. The one existing-test edit is justified.

There were no checkpoint findings to judge, because no checkpoint ran. Score: 8/10. The result is correct and well tested. It loses points because three developer attempts went to a ticket the factory already knew was the lead's.

French: none touched (factory only).

## Set aside
Nothing.

## Stop reason
None. No blocking or should-fix findings, so the loop ends after this round.

## Factory
- **Flow:** one plan, three failed developer attempts (two with no edit), one direction that waited about 1.5 h for Claude's window, and an Opus finish. No stops for the owner.
- **Models:** Opus planned it ($1.17), directed it ($0.62) and finished it ($2.09). Qwen spent about 1 h 50 min and merged nothing.
- **What to change:** the planner's routing. A phone regroup goes to the lead, or to the developer as a CSS-only ticket that copies note 13's example. This is the same lesson as F9 and F224: a rule that only lives in the lead's notes doesn't reach the planner's routing.
