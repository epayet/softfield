# Review: F95, sign-offs counted once, and the lead can look

- **Status:** done, signed off by the owner on 2026-10-16.

## Sign-off sheet

**Expected:** the Overview never shows more sign-offs waiting than the desk lists, and when you ask the planning room about what you see, the lead looks at the same page and data and answers with names.
**Done when:** Needs you on the Overview has no sign-off rows of its own (the desk's entry counts them); an ADR, a blocked ticket or Claude's reserve still show as before; planner and review jobs can read the database and any dashboard page, and change nothing.

### 1. What changed
- **Sign-offs show in one place: your desk.** Needs you on the Overview no longer lists "softfield signoff …" rows. A milestone waiting for your sign-off shows only inside "N things wait for you on your desk", the same count as the desk's "Finished, to talk through". The "2 to sign off, 1 on the desk" mismatch (F95, F107, F115) can't happen any more.
- The other Needs-you items (a decision to accept, a blocked ticket, Claude's reserve, a stopped runner) show as before. Phone notifications still tell you when a sign-off is new.
- **The lead can look.** When it answers on a planning thread or reviews a milestone, the lead can read the factory's database and any dashboard page as text, read-only: nothing can be pressed, approved or signed off from there. So "it says 2, I see 1" gets an answer with the names you see, not a guess.
- *(Fixed in this review)* The developer's version still showed a sign-off row when the milestone was not on your desk, which is exactly the F95 case (a milestone that got new tickets after its review). It now never does.

### 2. How to test it yourself
Restart the runner first: this review changed its code.
1. On your phone, open the Overview. Under Needs you, there is no "signoff" line; if something waits for your sign-off, it is inside "… wait for you on your desk".
2. Tap that line: the desk's "Finished, to talk through" lists the same number of milestones.
3. On `/planning`, plant a question about your desk, e.g. "what is waiting on my desk right now?". After the runner's next pick, the lead's reply names the items you see there.

### 3. Left for later
- Nothing from this card. A sign-off whose milestone isn't on the desk (it got new tickets after its review) now shows nowhere until those tickets are done and it ripens again; that is D1 as agreed, and the desk then lists it.
- Looking at a page as a picture (for "this looks bad" questions) stays in ADR 28's Later.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-10 and 13: six planner replies on the card's thread (Opus), settling ADR 28 with you.
- 2026-10-14 00:08, runner: f95-02 (the look command, protected runner code) merged first time as a headless lead ticket, 34 min ([session](../sessions/2026-10-14-0008.md)).
- 2026-10-15 16:36, runner: f110-01 (which f95-01 waited for) stopped twice on "no edit after 10 min", passed after the lead's direction; then f95-01 merged first time by the local model in 77 min. The Sonnet checkpoint read both ([session](../sessions/2026-10-15-1636.md)).
- Lessons:
  - **A developer can turn a ticket's rule into its opposite and still write green tests.** The Done when said "not on the desk: no row"; the developer wrote "not on the desk: its own row", with a test for it. The checkpoint read "tests both sides" and called it sound without comparing the test with the Done when. Fix: the checkpoint prompt already asks it to check the Done when; this is a missed one, scored as such.
  - **ADR 30 left two stale paths in the lead's own prompts.** The review and escalation prompts named `tests/unit` and `tests/integration`, which this project no longer has. Fixed here: they now name the project's own test folders.
  - The `look` command worked in this review: the job hours below came from it.
- 2026-10-15 21:44, runner: review round 2 (Opus) re-read round 1's own fixes; both hold, no new finding.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Let review jobs run `softfield report <key>` (asked in F31's review too): this job still couldn't write its own numbers block, the runner fills it.
  - The full test run (`tests/runner tests/factory_dashboard`) takes more than the 10 minutes a job's command may run, so a review can only run parts in the foreground. F71's study is where that is answered; until then, reviews run the touched files' tests plus the runner's.
  - A card's diff should be its tickets' commits, not everything since its start tag: this one's start tag holds ADR 30's whole move of `docs/` to `.softfield/`.

### 7. What clogged the factory line
From the jobs in the metrics database (read with `softfield look`):
- **f95-01 waited about a day and a half on f110-01** (f95-02 merged 14 Oct 00:42; f110-01 only ran on 15 Oct 16:36). The dependency was right (without f110-01 a sign-off would have shown on neither page); the wait was the queue's order. What unclogs it: nothing to change, the priority was the owner's.
- **f110-01 lost 20 minutes to two "no edit after 10 min" stops** before the lead's direction (1 min, $0.53) got it through. What unclogs it: the edit-stop is already under review in f93-01 (the owner set it to priority 0 on 15 Oct).
- **f95-01 took 77 minutes for an 18-line change**, of which gates 18 min. What unclogs it: nothing new; the local model's pace on dashboard tickets is known.

## What was built
- **f95-01** (`factory_dashboard/overview.py` `_live_context`): Needs you leaves out the stored `signoff` owner items, as it already left out `planning` ones (f6-09); `notify` still carries them all. Four tests in `tests/factory_dashboard/test_overview.py`.
- **f95-02** (`runner/look.py`, `runner/cli.py`, the planner's and the review's tool lists, the planner prompt's one line): `look sql` opens the database read-only with SQLite's authorizer allowing reads and schema PRAGMAs only; `look page` is one GET on the dashboard app in-process, with a test that no GET route writes. 23 tests in `tests/runner/test_look.py`, and the tool-list assertions in `test_loop.py` that no developer, checkpoint or escalation gets it.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | blocking | claude | f95-01 kept a sign-off row when its milestone was off the desk: the F95 case itself, against D1 and the Done when; its test asserted the opposite. It also added `Need.subject` and a second `live_line` per poll | Fixed: every `signoff` item left out of `needs`; `Need.subject` removed; `test_a_signoff_on_a_milestone_off_the_desk_shows_no_row` |
| F2 | should-fix | claude | The review and escalation prompts named `tests/unit tests/integration`, gone since ADR 30: the required command fails at once | Fixed: `{tests}` from `[checks] test_dirs` in `runner/prompts.py`, `runner/milestone.py`, `runner/loop.py`; asserted in `tests/runner/test_milestone.py` |
| C950-2 | nit | claude | The data-needs test only checked that "signoff" appeared somewhere | Confirmed and tightened: it asserts the item's own text |

Tests read: all four of f95-01's (one changed in meaning, one tightened, the other two kept), and f95-02's `test_look.py` and `test_loop.py` changes. f95-02's tests cover each refusal (writes, ATTACH, PRAGMA writes, two statements, a write hidden in a CTE) and check the file is unchanged afterwards. f95-01 changed no existing test, only added.

Checkpoint: one nit (C950-2), confirmed. It missed F1, which was in the diff it read.

French: nothing to check, the dashboard is English only and nothing under a locale changed. Screenshots: no browser in this job; the change only removes rows.

Checks after the fixes: `tests/factory_dashboard/test_overview.py` and `tests/runner/test_look.py`, 139 passed; the review and escalation tests of `test_milestone.py` and `test_loop.py`, 79 passed; ruff and mypy clean on every edited file. The full `tests/runner tests/factory_dashboard` run, started in the background after the overview fix, gave 2288 passed in 14 min 45 s (longer than one foreground command may run).

**Round 2** (only round 1's fix commit to read): F1 holds. Nothing else read `Need.subject`, and the off-desk test now asserts no row. F2 holds too: this round's own prompt named `tests/runner tests/factory_dashboard`. The review prompt has its own assertion in `test_milestone.py`. The escalation prompt has no assertion, but it would fail with a KeyError if `{tests}` weren't filled in, and the 18 escalation tests in `test_loop.py` pass. Checks: `test_overview.py`, `test_milestone.py` and `test_look.py` all pass (178 tests), plus the 18 escalation tests; ruff and mypy are clean on every edited file. No new finding, so the loop stops here.

Score: 6/10 (unchanged). f95-02 is careful work: a read-only guarantee SQLite itself enforces and a test that no GET writes. f95-01 got the card's one decision backwards and tested the wrong rule, and the checkpoint passed it.

## Factory
- **Flow:** two tickets, both merged first time; one waited on f110-01 (another card's ticket), which needed a direction. One checkpoint (Sonnet, $0.16), one review. No escalation, no stop for the owner.
- **Models:** Opus for the planner replies, the lead ticket and the direction; the local model (qwen3.6-35b-a3b) for f95-01 and f110-01; Sonnet for the checkpoint.
- **What to change:** F2 is fixed. The test-time limit and the start-tag diff are in "What next"; neither needs an ADR.

## Workflow observations
- The start tag holds ADR 30's move of every ADR and card from `docs/` to `.softfield/`, so the milestone diff is mostly someone else's work; the review read F95's two tickets' commits instead (as in F31's review).
- `softfield report` isn't in a review job's commands, so the numbers block below is the runner's to fill.

<!-- runner report -->
<!-- /runner report -->
