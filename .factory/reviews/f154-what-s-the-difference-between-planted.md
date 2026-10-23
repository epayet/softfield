# Review: F154, each board stage says what it means and what moves a card on

## Sign-off sheet

### 1. What changed
The board has five stages instead of six: Seed, Sprouting, Planted, Ripe, Harvested. Planted and Growing are now one Planted column, in the order the runner takes the work, so you can drag a card nobody has started above one that is half done. A card with work started stays in Planted and says so itself: an orange edge and a small "growing" tag with the plant drawing. The legend under the field explains the orange edge. Each column's head now has two lines: what a card there is ("in line for the factory, #1 first · 42, 15 growing") and what moves it on ("Next: every ticket done, then Claude reviews it"). On a phone, where the longer explanations are hidden, those two lines are still there. A card's page says "Stage Planted: in line for the factory · growing since 1 Oct 08:30" once a ticket has started.

### 2. How to test it yourself
1. On your phone, open the board: five plots (three on the first row, two on the second), Planted shown first.
2. Read the Planted head: what it means, how many cards and how many are growing, then the "Next" line. Tap Seed, Sprouting and Ripe: each says what it is and what comes next; Harvested has no "Next".
3. In Planted, find a card with the "growing" tag (F142, F5) and one without (F158, F159). Drag one without the tag above one with it, press Send new order: it shows on its way, and after the runner's next pick it stays there.
4. Open a growing card (F5): its Stage line says "Planted: in line for the factory · growing since …", and the steps at the top show the date on Planted.

### 3. Left for later
Nothing from this card. The board's intro still says the factory "grows" a card ticket by ticket, which now matches the tag; no change needed.

### 4. Decisions waiting for you
None. The one decision (one Planted column, the tag on the card) was settled with you on 2026-10-20 and is on the card.

### 5. How the work went
- 2026-10-20: planned with you in the Planning room (two planner jobs, $4.69; one planner attempt failed in between and was retried two hours later, after other work).
- 2026-10-23 02:37 ([session](../sessions/2026-10-23-0237.md)): 1 ticket, `f154-01-stage-says-what-next`, built by the lead in 22 minutes, first attempt, $3.38; 0 local tokens (a lead ticket by D5: one stage list read by three pages, a script and many tests).
- Lessons: the lead ticket touched every reader of the stage list and the live board confirms it (42 planted, 15 growing). The review only tightened two tests that the change had cut down to their first rows, the same slip F173's review fixed: an edited test that narrows its check to "the first N" when the list grows. Now a rule in `docs/agents/developer.md`.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** with one Planted line of 42 cards, the column is now taller than a phone screen; dragging a card from #40 to #1 is a long scroll. The ⋯ menu's Top and Bottom already do it in one tap, so nothing is needed now, but if you find yourself scrolling, plant "a Planted filter: growing only / not started" (it pairs with F146's "developer only" view idea). And F155 (no product vs factory on the board) is the next small board clean-up in your seeds.

### 7. What clogged the factory line
- Waiting on F152: f154-01 needed f152-01 first (the review line on a done card), and f152-01 took 4 hours on 2026-10-21 (a failed attempt, a 1 h 36 timeout, a failed last attempt, then the lead's escalation). Nothing sat idle (other cards ran meanwhile), but it held this card two days. What would unclog it: f152-01 was a template-and-test change near a stage list; tickets like it can go straight to the lead under "Who builds what" when they edit the same lines a lead ticket will.
- One planner attempt failed on 2026-10-20 at 09:15 and the retry waited until 11:13 behind a local developer job. A planner retry could go before a long developer job (the owner is waiting on a planner answer, nobody waits on the developer); worth a seed if it recurs.

## What was built
- `factory_dashboard/board.py`: `STAGES` is five; `WORDS` carries each stage's meaning and its next step (D2); `Card.started` marks a planted milestone with a ticket started or a running or stopped bug (D1); `running` (the "Now:" line) and F152's review step follow `started`, not a stage. `PLACED` and `RESERVABLE` lose growing, so the places and the "on its way" marks count across the one line.
- `templates/board.html`, `dashboard.css`: the `started` class keeps the orange edge, the `card-growing` tag, the "Next" line in each head (hazard tick only, as ornament), the legend's swatch, the phone order Ripe, Planted, Sprouting, Seed, Harvested, five plots in a row from 900 px (D3, D4).
- `milestones.py`, `templates/milestone.html`: five steps; the started date on Planted, "growing since …" on a started card's own step and its Stage line (D4).
- `line.py`: the floor's rows are the planted cards, the same cards as before. `board.js`: `PLACED` without growing. `stage_icon.html` keeps the growing drawing for the tag. Nothing in `runner/` changed; the runner's pick (`task_priority`) already ignores whether a card is started, so the board's single line is the real order.

Tests: new cases for each head's words and next step, the tag on started and not-started milestones and bugs, a planted card with nothing started and nothing left to do having no review step, and the card page's "growing since". Edited existing tests, each checked: every "growing" stage assertion became `("planted", True)`; the place and reorder tests now count one line of seven or eight cards, with F24 (priority 1) first; the browser drag tests drop a not-started card above a started one and scroll both cards into view, since one column is taller than a phone; the Overview's reserve list follows the new order (F24 before F23). The edits match D1 to D4; two had narrowed their check (F1, fixed).

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | nit | claude | Two edited reorder tests checked only the first five or six cards of eight | Fixed: both assert the whole Planted line |
| F2 | nit | claude | `ReserveLever`'s docstring and its comment in `thread.html` still said "planted or growing" | Fixed |

No checkpoint ran (a lead ticket), so there are no checkpoint verdicts. Score: 9/10: every decision built as written, every reader of the stage list found, and the live board matches the Done-when (the cards it named, F151 and F106, have since been harvested, so the drag was checked on F158 and F5 and in the browser tests).

Checked and fine: no `growing` stage left in `factory_dashboard/`, `runner/` or `docs/` (only the tag, its CSS and the drawing); `/board` read as text shows five stages, "42, 15 growing" and each "Next"; ruff passes and the runner and dashboard tests pass.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing new. The f172 nit in `docs/backlog.md` still says "every planted and growing card's doc"; it reads correctly as "every planted card's" and is left as written history.

## Factory
- Flow: planned 2026-10-20 in the Planning room, built 2026-10-23 by one lead job, first attempt, no stops for the owner, no limit waits, no parks. The wait was the dependency on f152-01 (see 7).
- Models: Claude Opus planned it ($4.69 over two planner jobs, one failed attempt with no cost recorded) and built it ($3.38); the local model had nothing to do, by D5.
- What to change: "an edited test narrowed to its first rows" has now come up in two reviews in a row (F173, F154), both from the lead's own tickets. Twice is a pattern, so this review added it to rule 13 of `docs/agents/developer.md`: when a list an existing test asserts grows, assert the whole new list, never its first rows. The lead reads the same rules for its own tickets.

<!-- runner report -->
<!-- /runner report -->
