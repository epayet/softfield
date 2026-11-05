# Review: F171 each card once on the board, and fix tickets named after what they fix

## Sign-off sheet

### 1. What changed
- **Each card shows once.** Travel-companion's board no longer has a second "F2" or "F4" with no title. Their tickets are back under the real cards, and F2 and F4 now read done with their titles.
- **No more empty cards.** Softfield's board and milestones list no longer show an untitled "F107". F29, F44 and F214 had the same kind of empty row and are hidden too.
- **Fix tickets have clearer names.** A fix ticket is now named after the ticket it fixes, such as `f179-05-fix-lead-split`, with `-tests` on a test-only fix (`f179-06-fix-lead-split-tests`). The name used to be the finding's first four words, so `f1-14-fix-the-been-test-does` stopped mid-phrase.
- **The letter now follows the project.** A note planted on a product project such as travel-companion becomes an `m` card. Softfield stays `f`, because its settings now say it is a factory project. Existing cards keep their keys, because a key is in the card's file name, thread, plan branch and ticket ids.
- **Reviews now know they can read the numbers.** Their instructions now say how. F19's, F28's and F135's reviews had written that they couldn't read the metrics database.

No pictures: nothing on the page was redesigned.

### 2. How to test it yourself
1. On the phone, open travel-companion's board. Each key shows once with its title, and F2 and F4 are among the done cards.
2. Open Softfield's board and its milestones list, and search for F107. It isn't there.
3. On travel-companion's Planning page, plant a short test note. When the runner has picked it up, the new card's key starts with `m`, not `f`. Set the card aside afterwards.
4. Next time a checkpoint files a fix ticket, check that its name repeats the ticket it fixes.

### 3. Left for later
- No tickets or bugs came out of this review. Two findings were fixed in it, and three small points are only noted here (see Findings).
- Travel-companion keeps its `f` cards, as decided in the plan (D5).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-22, outside the runner (no session report): `f171-01` committed directly, with Claude. Its first half (D1) landed separately as `fc0d827`.
- [2026-10-22 11:39](../sessions/2026-10-22-1139.md): `f171-02` and its fix `f171-05` merged by the local model, each on its second attempt (2.50M and 1.95M tokens in).
- [2026-10-23 06:53](../sessions/2026-10-23-0653.md): `f171-03` merged by the lead, $0.57.
- [2026-11-05 08:13](../sessions/2026-11-05-0813.md): `f171-04` merged by the lead, $0.33.
- Lessons:
  - **A test can pass because it looks for the wrong thing.** Both milestones-list tests looked for `F99` and `F98` among rows keyed `f99-empty` and `f98-empty`, so they could never fail. The checkpoint read them and called them sound. This review corrected them.
  - **The gates can't catch this.** "Fails without the change" is in the ticket's Done when, but nothing runs it. See What next.
  - **The stand-in checkpoint earned its place.** Copilot found a real gap in `f171-02` while Claude was limited.

### 6. What next
- **Product:** on hold, as you asked (2026-10-04).
- **Factory:**
  - Have the gates run a ticket's new tests against the code from before the ticket, and fail any test that already passes there. It would have caught both tests above without a review. I'd make it a ticket on the next factory card rather than here. It needs care, because a `tests_only` ticket's tests pass on main by design.
  - Keep a card's tickets together. See the first item below.

### 7. What clogged the factory line
- **`f171-04` waited 13 days, 2026-10-23 to 2026-11-05.** Its plan was approved on 2026-10-22, and about 50 other lead-ticket jobs ran in between. The ticket has no dependency and no priority, so its card's place on the board decided. The metrics database doesn't record why it stayed behind, so I can't say more. Until it merged, new product notes kept getting `f` keys. What would unclog it: once a card has started, its remaining tickets go before a later card's.
- **Reading without editing, 2026-10-22, 20 minutes:** the first attempt at `f171-05` stopped with no edit after 20 minutes. The rule that stopped it worked as meant. What would unclog it: nothing new, since this is the known local-model pattern and a second attempt passed.
- **The local model's working time, 1.5 hours:** two small dashboard tickets took 1.46 hours in total, 0.34 of it in failed attempts. That's acceptable by "slow and good beats fast and bad", and no change is needed.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `runner/metrics.py`, `runner/loop.py` (`f171-01`, D2): each ticket sync folds an empty short-key row into the project's one live card with that key, moving its tickets, jobs and findings. Travel-companion's database now has no short-key rows left.
- `runner/prompts.py` (`f171-01`): the review prompt names `softfield look`.
- `factory_dashboard/board.py`, `factory_dashboard/milestones.py` (`f171-02`, `f171-05`, D3): a row with no state, no tickets, no end date and no done status is not shown.
- `runner/loop.py` (`f171-03`, D4): fix tickets are named after the ticket at fault.
- `runner/planner.py`, `runner/requests.py`, `.softfield/project.toml` (`f171-04`, D5): a note with no area takes `area` under `[project]`, or product when it is missing. Softfield's says factory.

## Findings and resolutions
| Id | Grade | Finding | What happened |
|---|---|---|---|
| F1 | should-fix | The two milestones-list tests could never fail (wrong key) | Fixed in this review; the checkpoint should have caught it |
| F2 | nit | `milestone_rows` queried tickets inside its loop, with a dead branch; `board.py` selected `m.state` twice | Fixed in this review |
| F3 | nit | The filter also keeps a state-less empty row that is done or has an end date, which D3 doesn't mention, and no test pins it | Noted only: the live database has no such row |
| F4 | nit | No test covers a short row whose only card is removed | Noted only: the code is right |
| F5 | nit | A long ticket name can still stop mid-phrase after four words | Noted only: D4 chose this, and the ticket at fault is clear from the name |

**The checkpoint's finding:** `C1265-1` (rows with a status still appeared) is confirmed. `f171-05` fixed it.

**Tests a developer edited:** I read them all.
- `f171-02` and `f171-05` only added tests.
- `f171-03` renamed the expected ticket ids, as D4 requires.
- `f171-04` added `area = "factory"` to two fixtures, because the default changed.
- None of them lost an assertion.

**French:** no French text changed.

**Checks after this review's fixes:**
- With the filter switched off, both corrected tests fail; with it back on, they pass.
- Ruff and mypy pass on the changed files.
- The full `tests/runner tests/factory_dashboard` run hit its time limit at about 80%, with no failures before it was stopped. I then ran the files most likely to be in the part it missed, one batch at a time, and all passed: 200, 313, 207 and 96 tests. No single run covered everything, so the runner's gates are the full check.

## Factory
- **Flow:** no stops for the owner and no parked findings. The checkpoint was parked once while Claude was limited, and Copilot stood in.
- **Results and cost:** the planner cost $4.43 on Opus, and lead tickets $0.90 (Opus and Sonnet). The Sonnet checkpoint cost $0.18, and the local model and Copilot's stand-in cost nothing in dollars here. The local model needed a second attempt on both of its tickets.
- **Scope:** `f171-05` changed `milestones.py`, outside its `files:`. The finding's text named that file, but `fix_ticket` only lists the finding's own `file`. It did no harm, and the session report flagged it, so no change is needed.
- **What to change:** the test check under What next.
