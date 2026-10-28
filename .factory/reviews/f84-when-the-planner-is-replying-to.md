# Review: F84, Coming says which reply the lead is writing

- **Status:** review round 1 done. Both should-fix findings are fixed in the review, and one nit and one factory point went to the backlog. Waiting for your sign-off.

## Sign-off sheet

### 1. What changed
In the Planning room, Coming no longer says "the lead is writing its reply now" on every waiting box. The one thread the lead is answering comes first, with an orange "Writing now" label and edge, "the lead is writing this reply · 2 min in, about 4 min left", and a thin bar of time spent against a reply's usual length. Each other waiting thread says its place and about when: "next, after F84's reply · about 4 min", then "3rd in line · about 10 min", in the order the lead takes them. A look at a blocked ticket says "the lead is looking at the blocked ticket". A thread's page shows the same words on its "Next for the lead" line. The "The factory now" tile names the reply being written, linked to its thread, then "Then 2 replies in line, about 16 min for all." A reply held for Claude's limit, and a message the runner hasn't picked up yet, read as before and come after the line.

### 2. How to test it yourself
1. On the laptop, open Planning and write a short message on three cards' threads, one after the other.
2. At the runner's next pick, look at Coming: the first card is on top, labelled "Writing now", with how long it has run and about how long is left. The second says "next, after F…'s reply · about … min", the third "3rd in line · about … min".
3. Look at the "The factory now" tile: "Writing now: F…, <its title> · … in", the key links to the thread, and under it how many replies wait and about how long for all.
4. Open the second card's thread: its "Next for the lead" line says its place, not "writing". Open the first: it says the lead is writing this reply, in orange.
5. When the first reply lands, Coming moves up: the second card is now "Writing now".
6. Do steps 2 to 4 on the phone, and once in the light theme: the orange words should read clearly on the pale page.

### 3. Left for later
- A message the runner hasn't picked up yet still says "after F84's reply, ~4 min", as the card asked, though the threads already in line come first. In `docs/backlog.md`, with the fix (count the line).
- A check that sends a ticket like this one to the lead at planning, so a developer isn't sent work the rules say is the lead's. In `docs/backlog.md`, waiting for F143's new rule.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-26: Opus wrote the plan and the ticket ($1.51), after the planner's row waited three days for Claude's limit.
- 2026-10-27 ([session](../sessions/2026-10-27-2319.md)): the local model's two attempts failed: the first broke seven existing tests on guessed names, the second timed out after 78 minutes. The ticket then waited about 16 hours for a Claude direction.
- 2026-10-28 ([session](../sessions/2026-10-27-2319.md)): an Opus direction ($0.64), a last local attempt that read for 20 minutes and made no edit, then an Opus escalation that built it in 43 minutes ($3.79).
- Review, 2026-10-28: fixed Coming's order for held replies and the light theme's ink for the new words.
- Lessons:
  - The plan sent the ticket to the developer, though the Known range said a ticket that adds to `test_planning.py` across a page's functions is the lead's. This is the third time (F30, F172, F84). F143 rewrites that rule; the backlog has the check that would make it stick.
  - The two parks (three days for the plan, 16 hours for the direction) were Claude's limit. The work itself took an hour once Claude had it.
  - The lead's own build was close to the card. The review found only a sort order and a colour that hadn't been tried in the light theme.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:**
  - Let F143 (split `test_planning.py` by page) run soon: it ends the rule that keeps sending planning tickets to the wrong worker, and it makes them developer-sized.
  - Watch the new Coming during a long night of replies: if "about 1.6 h for all" turns out far off, the estimate could use the last 10 replies instead of the last 20.

### 7. What clogged the factory line
- **Parked for Claude's limit before the plan: about 3 days** (the planner's row was queued 2026-10-23 22:28, held until 10-26 17:00, answered at 23:31). To unclog it: ADR 20's reserve for planning, already in place; nothing new.
- **Parked for a Claude direction: about 16 hours** (2026-10-27 11:32 to 10-28 03:24, held until 23:50 by Claude's limit, then waiting its turn). To unclog it: route this kind of ticket to the lead at planning (backlog, after F143), which skips the direction altogether.
- **Failed attempts: about 2.2 hours** of the local model (33 min failed, 78 min timeout, 20 min no edit), nothing merged. To unclog it: the same routing check.
- **Waiting before the start: about 14 days** (planted 2026-10-09). The board's order put it there.
- No waits for you on this card.

## What was built
- `factory_dashboard/planning.py`: `Place` and `reply_line` (D1). For each thread with an open planner row, it says whether it is being written (its row's `started_job` is a live job) or its place among the rows not started, in `dispatch.plan`'s order, skipping rows that wait. The estimate (D2) is the running job's time left plus a planner reply's typical length for each reply ahead. `_typical` now takes a role and an agent (or any agent). `_next_reply` no longer says "writing" for every thread: it names the reply ahead. `coming` puts the placed threads first, then the plants, then the rest (D4). `factory_now` adds the `writing` block (D6), and the thread page reads the same place.
- `templates/planning.html`: the "Writing now" label, edge, words and time bar on Coming's box; the tile's two new lines. `templates/thread.html`: the `#waiting` line in Opus's ink when its reply is being written. `dashboard.css`: the `.writing*` classes.
- Tests (`tests/factory_dashboard/test_planning.py`): seven new tests on one fixture (`_line`), covering the order and words, a row not started, a look at a blocked ticket, a ticket job ahead, the thread pages, the tile, and held and unpicked messages. Three existing tests changed, each for the new words: a planner job with no row now reads "after the lead's reply" (and nothing says "writing"); f6's thread is "2nd in line" behind an older row; Coming's first box reads "next, after f1-04-live · any minute now". All three changes follow the card, and none was loosened.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | Coming put a reply held for Claude's limit before a message the runner hasn't picked up, against D4 | Fixed: held threads come last; the held-and-unpicked test now checks that order |
| F2 | should-fix | claude | In the light theme, the "Writing now" label was pale text on orange, and the orange words were about 2:1 on a white plate | Fixed: the label takes `--hazard-ink`, the words and the tile's key a new `--opus-ink` token (Opus's colour in the dark theme, #b25a14 in the light, about 4.8:1); a test checks the thread's words use it |
| F3 | nit | backlog | A message not yet picked up says "after F84's reply, ~4 min" while the threads in line come before it | In `docs/backlog.md` with the fix; D3 asked for today's words there |
| F4 | should-fix | backlog | The plan routed a ticket the Known range calls the lead's to the developer, a third time | In `docs/backlog.md`: a `check-tickets` check once f143-05 has rewritten the rule |

Checkpoint verdicts: none. No checkpoint read this work: it was the lead's escalation.

Score: 7/10. The build matches the card closely, with good tests on real queue rows, and the review found only two small fixes. It lost points for the route: three local attempts, two parks and $4.43 of Claude, all after a rule said this was the lead's.

Checked and fine: a thread with a second message queued while its reply is being written stays "Writing now" and takes no second place. A typical of zero can't divide the bar (a zero `timedelta` is false in the template). A job past its typical length reads "any minute now". A planner job whose row isn't found falls back to "the lead's reply". A blocked-ticket row takes a place in line but matches no Coming box, which is right: it holds the lead too.

Tests: the whole `tests/runner tests/factory_dashboard` run reached 2,477 passed with none failed. Then it hit this job's 20-minute background limit inside `test_planning.py`; the one `E` was the stop itself. `test_planning.py` then passed in full (239) after F1's fix. The F84, Coming and theme tests (`test_planning.py`, `test_app.py`, `test_line.py`) pass after F2's fix, and so do the seven files after `test_planning.py` (179). Ruff and mypy are clean on `factory_dashboard`. The runner's gates run the whole suite before any merge. The rest of this diff range belongs to other milestones (F38, F68, F69, F80, F82, F164 and others) and their own reviews.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
- [f84-F3] An unpicked message's estimate ignores the line (with the fix).
- [f84-F4] The routing check, after f143-05.

## Factory
- Flow: one developer ticket, three failed local attempts, one Opus direction and one Opus escalation, two parks for Claude's limit (3 days for the plan, 16 hours for the direction). No checkpoint, no stops for you.
- Models: Qwen3.6 35B, about 2.2 hours of model with nothing merged. Opus: $1.51 for the plan, $0.64 for the direction, $3.79 for the escalation that built it.
- What to change: route at planning by a check, not a line in `lead.md` (F4). The escalation's Known range line already says so; F143 sets the rule the check would hold.

<!-- runner report -->
<!-- /runner report -->
