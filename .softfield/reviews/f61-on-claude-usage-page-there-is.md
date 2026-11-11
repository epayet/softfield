# Review: F61, Claude's meters say when the window runs out at this rate

## Sign-off sheet

### 1. What changed
Under each of Claude's two meters on the Overview (the 5-hour window and the week), one new line says how the window ends at the current rate:
- "at this rate: out Fri 13:38, 3 days 3 h before the reset", in the warning ink, when it would run out before its reset (the time alone when it's under 24 hours away; minutes when the gap is under an hour; "out any time now" once that time has passed);
- "at this rate: lasts to the reset, about 54% by then", in grey, when it wouldn't.

A hatched ghost on the meter runs from today's fill to where the meter will be at the reset (to the end when it runs out). The legend has a line for it. There is no line or ghost in the first 10% of a window (30 minutes, or about 17 hours of the week), on a reading from before the last reset, or on Copilot's month.

The merged version drew the ghost only when the window ran out, and its words were wrong past 24 hours (for the card's own example it would have said "-3 days 44 h before the reset"). The review fixed both, so what you'll see is the version above.

### 2. How to test it yourself
1. On your phone, open the Overview and find Agent allowance.
2. If the week is more than about 17 hours in, under the week's meter: one line starting "at this rate:", and a hatched stretch on the meter after the coloured fill.
3. Work it out roughly: the week's percentage divided by the hours since the week started, times the hours left, plus the percentage now. That's the "about N% by then", or, past 100%, the line says "out" with a time.
4. Same check under the 5-hour meter once it's more than 30 minutes into its window.
5. Copilot's month shows no such line.
6. Switch to the light theme: the "out" line is a readable dark amber, not pale yellow.

### 3. Left for later
Nothing.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-10 18:27 ([session](../sessions/2026-11-10-1827.md)): 1 ticket, `f61-01-at-this-rate`, built by the local model on its third attempt after the lead's direction. Attempts 1 and 2 stopped at "no edit after 20 min" (it only read files), then the ticket waited about 4 hours for Claude's reset for its direction; attempt 3 took 75 minutes and 6.6M local tokens.
- The review (2026-11-11, Claude) rewrote about half of it: the ghost's width, the wording, the styling and the tests (findings F1 to F5).
- Lessons: the gates passed because the developer's own tests checked only that some line and some ghost exist. A ticket whose Done-when names exact words ("3 days 3 h before the reset") should say "assert the whole line" in its tests list, so the local model can't satisfy it loosely.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** the same line under Copilot's month is one call now (`_rate_line` with a month's length) if Copilot ever runs short. More useful: the runner could read this forecast itself and hold planner jobs when the week is "out" before its reset, which is what ran the week dry in October (D2 says the line isn't a hold; that would be a new card, worth planting if you want it).

### 7. What clogged the factory line
- About 40 minutes on two attempts that never edited a file (the model read the 2,700-line test file and the card again and again). The lead's direction fixed that; the "no edit after 20 min" stop worked as designed.
- About 4 hours parked waiting for Claude's 5-hour window to reset before the direction could be written. Unclog: the direction is a small, cheap Claude job ($0.47); it could run on the reserve rather than wait, as planner jobs do.
- The third attempt's 75 minutes produced work the review had to redo; the owner's "who builds what" rule would have sent a ticket with this much exact wording to the lead after the second failed attempt.

## What was built
- `factory_dashboard/overview.py`: `forecast(value, read_at, resets_at, length, now)` (D2, D3), pure, returning the out time (or none) and the use at the reset capped at 1; `_gap` (D1's rounding) and `_rate_line` (D1's words). `WindowAllowance` gains `read_at` (the reading's ISO time), `rate`, `rate_out` and `ahead`; only Claude's rows on a fresh reading get them (D5, D3).
- `_partials/allowance.html`: the ghost span under the fill, sized by `ahead`; the line on its own row at the end of the meter's words, after f9-29's (D6); the legend line (D4).
- `dashboard.css`: `.meter > .ahead` and `.swatch.ahead` as in the mock-up (`--ghost` over `--plate`, a rule-coloured inset edge); `.rate` full-width mono, `.rate.out` in `--warn-ink`.

Tests (`tests/factory_dashboard/test_overview.py`): the card's worked example to the second and its words; the mock-up's 5-hour case ("out 00:44, 5 min before the reset"); a window that lasts (words, grey, ghost at 54%); the 10% rule at 22 and 30 minutes; a zero reading; an out time already past; the gap's rounding (six cases); both Claude rows on the page with their words, ink and ghost width, and Copilot at 90% late in its month with none; a stale reading well into its window and a missing one with none; the legend's line. The developer edited no existing test; it only added the f61 tests, which the review replaced.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | The ghost's width came from the line's warn flag (true/false), so a window that lasts never showed its ghost | Fixed: `ahead` carries the projected use |
| F2 | blocking | claude | No gap under 24 h; no weekday and a negative, garbled gap past it; no minutes | Fixed: `_rate_line`, `_gap` |
| F3 | should-fix | claude | Tests pinned neither words nor width; the stale test passed by the 10% rule, not the stale check | Rewritten, failing on the merged code |
| F4 | should-fix | claude | `--hazard` instead of `--warn-ink` (unreadable in the light theme), ghost 1px past the track, line before the reset words | Fixed to the mock-up |
| F5 | nit | claude | An unused float `read_at`, a second parse of `at`, duplicated maths | Removed |

All five are in one file set and were faster to fix than to describe in tickets; F1 and F2 needed the rest rewritten around them, and the owner's rule prefers the lead finishing over a fix ticket on a poor branch.

No checkpoint ran, so there are no checkpoint verdicts. Score: 4/10: the forecast's maths was right and the 10% and stale rules were in place, but the two things the owner would see (the ghost and the words) were both wrong, and the tests were too loose to notice.

Checked and fine: the reading's time and the reset are both local (`queries.local`), so the out time prints in local time; `forecast` with a stale reading is never reached (`status` is set first). ruff, ruff format and mypy pass; `tests/factory_dashboard/test_overview.py` and `test_app.py` pass (367 tests). The full `tests/runner tests/factory_dashboard` run was stopped by the review's 10-minute limit at about 62%, with no failure up to there; the runner's own gates run it in full before merging.

The French: no `coucou/locale/fr/` change in this milestone.

The card's after pictures: none.

## Factory
- Flow: one developer ticket; two attempts stopped for not editing, a 4-hour park for Claude's reset before the direction, a third attempt that passed the gates. No stops for the owner.
- Models: the local model (qwen3.6-35b-a3b) built it on attempt 3, with 7.7M tokens in over three attempts; Claude Opus wrote the direction ($0.47) and the review.
- What to change: the gates trusted the developer's own tests. For tickets whose Done-when quotes exact words, the ticket writer (the lead) should list the exact assertions in the ticket so the local model writes tight tests. Once is not a pattern yet; if a second review finds loose tests on worded UI, it becomes a line in `runner/instructions/task-format.md`.

<!-- runner report -->
<!-- /runner report -->
