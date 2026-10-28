# Review: F51, the desk counts only what waits on you

- **Status:** review round 2 done, the loop stops: all four round 1 findings are fixed and checked, with nothing new. Waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- **One box per card on your desk.** A card's ADR, plan, mock-ups and merges now make one item under "Proposals to review", not one each. The item shows its parts in the order you settle them (ADR → plan → mock-up → merge), each marked "on its way" once you've pressed it. While the ADR is still open it says "accept the ADR first". It counts as one on the Planning tab and in Needs you, and stops counting once every part is on its way. The general thread's ideas and merges stay one item each, since each has its own button.
- **Approve plan right after Accept ADR.** Once you've pressed Accept ADR, the plan's Approve button works straight away. It says "ADR N's acceptance is on its way: the runner applies it first". At its next pick the runner accepts the ADR, then approves the plan. If the accept fails, the runner refuses the plan ("relies on ADR N, still Proposed: accept it first") and leaves main as it was.
- **Answered is answered.** A thread you've replied to leaves "Your answers wanted" at once and shows only in Coming until the lead replies.
- **A lead reply with no proposals no longer hides the earlier ones.** They keep their buttons, on the thread and on each proposal's page.

### 2. How to test it yourself
1. On the phone, open Planning after the next runner restart (the dashboard you have open still runs the old code: today it shows F61's mock-up and plan as two items).
2. Under "Proposals to review", find a card with a plan and a mock-up (F61, F86, F97 or F146): it is one item, with small "PLAN → MOCK-UP" tags, and the Planning tab's number is lower than before.
3. Find a card with an ADR and a plan: its item says "accept the ADR first" and opens on the ADR. Press Accept ADR.
4. Go back to the desk: the item now opens the plan, and the ADR tag says "on its way". On the plan's page, Approve plan is not greyed, and the line under it says the acceptance is on its way. Press it: the item turns dashed and leaves the count.
5. At the runner's next pick, check the card's thread: the ADR is accepted, then the plan is approved and its tickets queued.
6. Reply on any thread in "Your answers wanted": it leaves that list at once and shows in Coming only.

### 3. Left for later
- **F51's replan is still open on your desk:** "F51: one box per card, the conversation and its proposals together", with the mock-up "Your desk: one box per card". It came from F176 (bundle the conversation with its proposals) and goes one step further than what was built here. Approve or send it back from F51's thread.
- Nothing new in `docs/backlog.md`.

### 4. Decisions waiting for you
None from this review.

### 5. How the work went
- 2026-10-08 to 10-20: Opus wrote the plan and replanned it twice as F99, F105 and F157 were merged in (four replies, $12.29).
- 2026-10-23 ([session](../sessions/2026-10-23-1549.md)): the local model passed f51-03 (a 7-line fix) at the first attempt. The Copilot checkpoint found its test didn't check the button. The local model then passed the fix ticket, f51-04, at the first attempt too.
- 2026-10-27: Opus wrote a third replan from F176 ($7.60). It is still open (see 3).
- 2026-10-28 ([session](../sessions/2026-10-28-0900.md)): Sonnet did both lead tickets, f51-01 and f51-02, right the first time ($0.76 and $0.39).
- Review, 2026-10-28: round 1 fixed the runner guard's reach, the doubled card name on the desk, a weakened test and a duplicate test. Round 2 checked those fixes and found nothing new.
- Lessons:
  - **Sonnet's lead tickets were right but loose at the edges.** It did the right thing in the code, then took the easy way at three edges: it pinned doubled text in a test instead of reading real titles, weakened an old test to `!=`, and widened a guard past what D3 said. The Known range now has a line on Sonnet as the lead.
  - **The planning cost more than the build.** Five Opus replies ($19.89) against $1.15 for the two lead tickets, and the local model built the rest for free. F177 (record each job's real cost, late planner replies start fresh) is the card that looks at this.
  - **The checkpoint that read f51-03 missed a test that repeated another,** though its docstring said so. Small, and fixed.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:**
  - Settle F51's open replan next: it is the "conversation and proposals in one box" you asked for in F176, and it reuses this milestone's bundle.
  - A plan's title already names its card in nearly every reply. Text to plant if you'd like it settled once: "A plan's title is just what it does; the dashboard adds the card's name wherever it is shown."

### 7. What clogged the factory line
- **The plan, three times over: about 12 days** (planted 2026-10-08, the last replan before the build on 10-20). Each merged card (F99, F105, F157) changed the plan. To unclog it: nothing to change. Merging cards into one plan is what you asked for.
- **Waiting between the halves: about 4.6 days** (f51-04 merged 2026-10-23 20:12, f51-01 started 10-28 11:56). F68, F69, F80, F82 and F84 ran in between, ahead on the board. To unclog it: nothing. The board's order decided.
- **No failed attempts, no parks, no limits hit, no waits for you** during the build.

## What was built
- `factory_dashboard/planning.py`:
  - `_bundle` and `_part_name` make a card's open proposals one `DeskItem` with `parts` (name, on its way), ADR first. It links to the first part still open.
  - `_open_proposals` bundles every thread except the general one.
  - `_answers_wanted` drops a thread with an open `plan_message`.
  - `_adr_waits` takes the ADRs with an open `accept_adr` (D2), and `proposal_review` passes them and says so.
  - `_has_proposals` skips a `'[]'` reply (D5).
- `factory_dashboard/templates/planning.html`: the parts as tags on the desk item. `proposal.html`: the "on its way" line under Approve plan.
- `factory_dashboard/overview.py`: a notice counts a bundle's parts still to do ("2 proposals to review"), so one notification per card still says what is in it. Checked: that is the existing notification test's wording, and one notice per card is unchanged.
- `runner/requests.py`: `_proposed_adrs` refuses a plan whose drafted ADR is still Proposed after the merge (D3). The review narrowed it to ADRs new to main (F1).

Tests: desk bundling (ADR, plan and merge in order; plan and mock-up; the general thread's ideas stay apart), the count going 1 → 1 → 0 as parts go on their way, an answered thread leaving the desk, Approve plan enabled by an open accept, the runner applying accept then approve in one pick and refusing a plan whose ADR stayed Proposed, and an empty reply keeping the earlier proposals. f51-01 edited three existing tests: two for the one-item desk (right), and F35's trail, which it weakened (F3, fixed).

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The runner's guard refused a plan for any Proposed ADR it touched, not only one it drafted. A plan editing ADR 23 or 27 on main would be refused while its Approve button stays enabled | Fixed: only paths new to main are checked. A new test merges a plan that edits ADR 23 on main; it fails on the old code |
| F2 | should-fix | claude | A card's desk item doubled its name ("F69: F69: the button becomes…"). 13 of the last 15 plan titles already start with their card | Fixed: the name is added only when the title lacks it. The tests hold both cases |
| F3 | nit | claude | F35's Previous/Next test was weakened to `next != F6's plan` | Fixed: asserts `/planning/m4` |
| F4 | nit | claude | f51-03 added a test repeating an existing one | Removed |

**Round 2** (fix diff `e80be04`, the review's own fixes; no fix tickets ran in between):
- F1 holds up against `_accept_adr`. A successful accept writes the ADR to main as Accepted, so the guard doesn't need to check it. A failed accept is undone, so the ADR is still new to main and the plan is refused. Tests cover both cases.
- F2's word boundary keeps a near-miss prefixed: on F6's card, "F60 plan" shows as "F6: F60 plan".
- F3 and F4 are as described. Nothing new found.
- Tests: `test_requests.py`, `test_planning.py` and `test_overview.py` pass again (675 tests, 9 minutes). The full `tests/runner tests/factory_dashboard` run passed every test up to 86%, then hit this job's time limit and was stopped, as in round 1 (the `E`s were printed as it was killed). The runner's gates run the whole suite before any merge.

Checkpoint verdicts: C1366-2 confirmed (the empty-list test didn't check the proposal kept its link and state; f51-04 fixed it). F4 was missed by the checkpoint that read f51-03. F1 to F3 were in f51-01 and f51-02, which no checkpoint read before this review.

Score: 7/10. All four tickets were right the first time. The bundle, the accept-then-approve order and the runner's guard follow the decisions, and the runner test proves the order end to end. Points off for the doubled titles, which any look at real data would have shown, the guard reaching past D3, and two loose tests.

Checked and fine:
- Requests are applied oldest first, so an accept pressed before Approve plan lands first; the runner test covers it.
- A bundle whose ADR is on its way no longer says "accept the ADR first".
- A merge alone keeps its "merge X into Y" words.

Tests: `tests/runner/test_requests.py`, `test_planning.py` and `test_overview.py` pass after the fixes (675 tests). Ruff and mypy are clean on the changed files. The full `tests/runner tests/factory_dashboard` run hit this job's 10-minute limit at about 98% and was stopped (the `E`s printed as it was killed, as in F82's review). The runner's gates run the whole suite before any merge. The rest of this diff range belongs to other milestones and their own reviews.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing new.

## Factory
- **Flow:** two local tickets, each passed at the first attempt, with one Copilot checkpoint finding between them. Two Sonnet lead tickets, both right the first time. No stops, parks or limits, no interventions from you.
- **Models:**
  - Qwen3.6 35B: about 32 minutes of model for f51-03 and f51-04.
  - Sonnet: $1.15 for the two lead tickets, including protected runner code.
  - Opus: $19.89 for five planner replies.
- **What to change:**
  - The Known range now notes Sonnet's loose edges as the lead.
  - A Sonnet lead ticket's own tests deserve a checkpoint like any other. None ran between f51-01, f51-02 and this review, because the review came straight after.
  - The planning cost is F177's to look at.

<!-- runner report -->
<!-- /runner report -->
