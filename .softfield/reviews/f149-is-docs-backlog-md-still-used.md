# Review: F149, retire the backlog file

## Sign-off sheet

**Expected:** no review in any project writes a backlog file again, and Softfield's is gone, each item a bug seed on the board, a planted card, or dropped with its reason.

**Done when:**
- The prompts never name a backlog, and a test guards that: **met**, and the test is stronger after this review.
- Softfield's file is gone, and the board shows the new seeds and cards: **met**.
- The next review sets aside a ticket for a nit worth fixing and says the others in its report: **met**. F139's review already did this (bug-55, and its findings F4 to F6 reported only).
- Travel Companion's and Coucou's files go through their own cards: **in hand, not finished**. Both cards exist, and Coucou's file was still there when I looked.

### 1. What changed
- `docs/backlog.md` is gone from Softfield. Nothing on the dashboard ever showed it.
- A review's small finding now becomes a bug seed on your board, if it's worth a run. If it isn't, it's said once in the review report.
- Five new bug seeds (bug-49 to bug-53) and three new idea cards (F200 to F202) are on the board.
- This review also fixed something you could have noticed: a point set aside as a seed no longer keeps its review going for another round, and a review is no longer told to fix another milestone's finding. This one was told to fix F139's bug-55.

Mum will notice nothing.

### 2. How to test it yourself
1. Open the board on the dashboard and find the Bugs seeds: bug-49 to bug-53 should be there, not queued.
2. Find the idea cards F200, F201 and F202, and open F200: it should talk about giving reviews a ready-made hours block.
3. Open F149's card and read "Done": every item of the old file is listed with where it went.
4. At the next milestone that sets a should-fix point aside, check that its review stops without an extra round for that point.

### 3. Left for later
- **Bug seeds:** bug-49 (two timing tests that fail now and then), bug-50 (a parked checkpoint restarts on every merge), bug-51 (a test for escaped HTML on every page), bug-52 (a gone merge listed under Set aside), bug-53 (an old ADR or merge doesn't say its age).
- **Cards:** F200 (where the hours went), F201 (pages render their markdown), F202 (while main's tests fail, hold every ticket but the mender; it amends ADR 29 item 7). One more note went onto F143.
- **Other projects:** Coucou's F1 and Travel Companion's F10 retire their own files.
- **bug-55** (F139's) stays set aside. The review prompt listed it as "fix these yourself", but that was the fault fixed here, so I left it.

### 4. Decisions waiting for you
None. ADR 35 was accepted on 2026-10-28.

### 5. How the work went
- 2026-10-27: planned by the lead, with ADR 35 and two lead tickets.
- 2026-11-02: terminal session, both tickets merged as one commit by the lead, with no developer involved and nothing for the local model. Lead and local token counts aren't split for it, because the database has no job for that session.
- 2026-11-03: this review, one round. It fixed five findings itself and reported one.

Lessons:
- **A new route needs tracing through everything that reads the old one.** F149 changed the route's name, but the loop's counting ignores routes. f139-F3 then came back as "recurring". `Finding.holds_review` now covers this.
- **`actionable` couldn't simply be changed.** A stand-in checkpoint's findings also carry `report` and still need their fix tickets, so the new rule sits beside it.
- **Check for the word, not the path.** The ticket's check ruled out `docs/backlog.md`, so "the backlog items" survived in the same document. The guard test now looks for the word in the whole of both modules.

Session reports: [`.softfield/sessions/`](../sessions/).

### 6. What next
- **Product:** nothing proposed, as product work is on hold.
- **Factory:**
  - F202 is the seed I'd queue first among these: every developer ticket that starts while main is red spends a full model run before it waits. It needs a short ADR, as it amends ADR 29 item 7.
  - bug-49 next: those flaky tests have already paid for one Opus step-up.
  - Add one line to the lead's review craft: when a change adds a route or state, check who reads it.

### 7. What clogged the factory line
The database records only two jobs for this card: the plan (about 4 minutes on 2026-10-27) and this review. So I can't give you real hours for the rest.
- **Five days between the ADR's acceptance (2026-10-28) and the build (2026-11-02):** the card waited for its turn, as far as I can tell. I didn't break those days down, and limit waits aren't recorded per card. F200 would make this answer ready-made, though it wouldn't split a card's waiting time by itself.
- **The build:** a terminal session, so its hours aren't recorded at all. Suggested fix: when a terminal session merges a card's tickets, its closing note gives the time spent, which the sheet can then quote.

## What was built
- **f149-01:** `later` and `report` replace `backlog` in the review and checkpoint prompts, the re-review scope, `ROUTES` and the docs. Old files that say `backlog` still read.
- **f149-02:** the file was deleted, and its items became seeds, cards, a note on F143, or were dropped with a reason on F149's card. I checked every item in the old file's Softfield sections against that list, and all are accounted for. f13-F4 went into f71-03.
- **Coucou's items:** I spot-checked m2-F6 and the product name, and both are in Coucou's own file.

## Findings and resolutions
| Id | Severity | Route | Finding | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | A should-fix point set aside still counted as open, forcing rounds and coming back as recurring | Fixed: `Finding.holds_review`, used by `update_seen`, `stop_reason` and the round count; tests added |
| F2 | should-fix | claude | The recurring list named other milestones' findings (older than F149) | Fixed: `recurring_for_claude` takes the milestone; test added |
| F3 | nit | claude | `docs/workflow.md`'s Report paragraph still said "the backlog items" | Fixed |
| F4 | nit | claude | The guard test missed prompts built in functions, and no test parsed `later` | Fixed: it reads both modules' whole source; `later`, `report` and `backlog` are parsed in a test |
| F5 | nit | claude | Card F200 claimed reviews have no query command, untrue since ADR 28 | Card rewritten |
| F6 | nit | report | The new seeds keep the old file's "Stays:" and "Next:" lines | Reported only: the Goal and Done when decide the work |

**One thing still stands after F1 and F2:** the saved count for f139-F3 stays at 2. If F139 gets another review round, it will be listed as recurring there, on its own milestone. That's harmless, so I didn't edit the runner's state for it.

**Checks:**
- `tests/runner`: 1,825 passed.
- `tests/factory_dashboard`: 1,132 passed. Both ran with this round's changes, in two separate runs on eight workers.
- ruff passes on the four changed Python files, and mypy on the two runner files.
- I didn't run the new tests against the old code to see them fail first. The two signature and `holds_review` changes mean they can't pass without the fixes, and the guard test can only fail if the word returns.

**French:** none in this milestone.

**Existing tests changed:** `test_a_checkpoints_findings_are_numbered_in_order` now expects `report` as the default route, which is the point of the change. Other tests keep `backlog` in their fixtures, which is still accepted and covers old files.

**Checkpoints:** none ran, as both tickets were the lead's, so there is nothing to judge or mark as missed.

**Score:** 7 of 10. The file and the prompts were retired cleanly and every item is accounted for, but the new route wasn't followed into the loop's counting.

## What was set aside
No new seeds from this review. The milestone's own are listed in "Left for later".

## Factory
- **Flow:** no stops, no interventions from the owner, no parks. The review took one round.
- **Models:** Opus planned and reviewed. The lead built in a terminal session. No developer or local model ran, as the plan decided (protected code, and a file to delete).
- **To change:**
  - Terminal builds leave no job in the database, so a card built that way has no cost or hours to report. The closing note in section 7 is the small fix.
  - The first scope worked well: it found this card's one commit among others in the range, including the two ticket ids it held.

## Workflow observations
- This review's own prompt showed the fault it then fixed, which is a good reason to read the prompt as evidence as well as instructions.
- Findings on the new routes so far: 2 `later` and 11 `report` in the database. Worth rereading after a few more milestones, to see whether `report` is swallowing things worth a run.
- ADR 35 item 3 (an idea as a quoted line in "What next") depends on f164-01, which is still in the ready queue. Until it lands, the prompt doesn't ask for that.

<!-- runner report -->
<!-- /runner report -->
