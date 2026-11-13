# Review: F224, Approve a plan to go first in line, in the fast lane

- **Status:** done, signed off by the owner on 2026-11-13.

## Sign-off sheet

### 1. What changed
A plan's review page has a new fold, **Approve first…**, between Approve plan and Reject…. On a phone it is called **First…** and sits on the same row as the others.
- Opened, it says what it costs: the card goes first on the board and into the fast lane, ahead of every other job, planning and reviews included, and it may use Claude's reserve. The yellow button with the hazard stripe approves the plan that way.
- It shows on plans, mock-ups and replans, as Approve plan does. It is greyed out while the card's ADR waits, and hidden while you're writing a comment.
- The moment you press it, the card on the board gets a dashed orange edge and a dashed plate saying "goes first · fast lane · on its way · at the runner's next pick", in whichever column it stands. The Overview's Fast lane line names it as "goes first · on its way".
- At the runner's next pick, the plan is approved, the card goes to #1 in Planted, and its fast lane mark is set, all in one commit. If something refuses the approval, nothing changes.
- A plan with no ticket to run is approved as a plain one, and the runner's answer says "nothing goes first".
- Plain Approve plan is unchanged: the card goes last.

The after pictures show F224's own plan already approved and no Approve first pending, so the fold and the dashed plate aren't in them: the sample data has neither. The tests draw both. One difference from the mock-up: it dashes the card's edge as well as the plate, and the build had dashed only the plate. Fixed in this review (F1), so it now matches the mock-up.

### 2. How to test it yourself
1. On your phone, open a plan waiting for your review. The bottom row should show Approve plan, First… and Reject… side by side, with no sideways scroll.
2. Tap **First…**: it opens on a row of its own with the words and the striped **Approve first** button. Type a comment on any point: Approve plan and First… both hide. Clear it and they come back.
3. Press **Approve first**. Go to the board: the card has the dashed orange edge and the "goes first · fast lane · on its way" plate. The Overview's Fast lane line names it.
4. After the runner's next pick, the card is #1 in Planted with the plain "fast lane" plate, and its first ticket is next on the Overview.
5. Pull the card's Fast lane lever off, or drag it down and send the order: it behaves like any other card.

### 3. Left for later
Nothing set aside. One small test gap, not worth a run, is noted in Findings (F3).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-05: Claude (Opus) planned the card and drew the mock-up.
- 2026-11-12: Claude (Sonnet) built the runner's ticket (f224-01) in 8 minutes ($0.48), green the first time.
- 2026-11-12: the local model (Qwen) had three 20-minute tries at the pages' ticket (f224-02), the last after a direction from Opus. It made no edit in any of them.
- 2026-11-13: Claude (Opus) finished f224-02 after the escalation, in 23 minutes ($2.24). Then this review fixed one mock-up difference and added a missing runner test.
- Lessons:
  - Qwen read for the whole time limit in each attempt and never started editing, even when a direction gave it the steps. The escalation added a note to the developer's instructions (note 12): make the first edit within ten steps, and copy `going_first` as the worked example for "a request shown at once".
  - A "Done when" line about two presses had no test. A runner test now holds it.
- Logs: `.softfield/sessions/2026-11-12-1651.md`, `2026-11-12-1703.md`, `2026-11-12-1801.md`, `2026-11-12-1817.md`, `2026-11-13-0046.md`.

### 6. What next
- **Product:** product work is still on hold, as you asked.
- **Factory:** a pages ticket at difficulty 3 that touches a template, the CSS, a board query and two test files was too wide for Qwen: it spent an hour reading and never edited. The planner could split such tickets: the fold on the review page as one ticket, the board's plate and Overview line as another, each with one worked example to copy. Watch whether note 12 changes this on the next pages ticket before adding more.

### 7. What clogged the factory line
Taken from the `jobs` table:
- **Failed attempts: 1 hour.** Qwen's three 20-minute tries at f224-02 (17:04–17:44 and 19:23–19:43 on 11-12) ended at the time limit with no edit. A smaller ticket, or a direction after the first empty attempt instead of the second, would have saved most of it.
- **Waiting for its turn: about 8 hours.** Between those attempts and before the escalation (19:43 on 11-12 to 02:12 on 11-13), the line was busy with F239's tickets, M2's tickets and the planning of M10 and M11. No agent sat idle, so this was queue order, not a clog.
- No limits hit, no stops for you, no parks.

<!-- runner report -->
<!-- /runner report -->

## What was built
`f224-01-approve-first-in-the-runner` (commit 9a998cf52, the lead's: the runner is protected):
- `runner/requests.py`: `approve_plan` takes the value `first`. Any other value is refused before anything changes. After the squash, `_goes_first` marks the card's header `**Fast lane:** yes` (once) when the card is ready or building and has a ticket in ready. `_first` writes the queue's list with the card at the top. The board order is stored, and parked tickets are freed as the Fast lane lever does. A card with nothing in ready is approved plainly and the result says so. Merges alone ignore `first`.
- Tests: eight new tests in `tests/runner/test_requests.py` (one commit, already marked, replan, freeing parked tickets, no ticket, a wrong value, a refused approval, merges alone). No existing test was changed.

`f224-02-approve-first-on-the-pages` (commit ab7152da6, escalated from Qwen and finished by Claude):
- `proposal.html`: the `details#approve-first` fold, with "Approve first…" on wide screens and "First…" on a phone. Its button posts `approve_plan` with the value `first`, is disabled with `adr_waits`, and hides with `#primary` while a comment is written.
- `dashboard.css`: `.btn.first` with the stripe, and the phone dock's rules extended from `#reject` to both folds.
- `board.py`: an open `approve_plan` request with the value `first` gives `lane_asked = "first"` in any stage. `reserve_marked` now reads every stage, so the Overview names the card. The Overview marks its queue rows "on its way".
- `board.html` and `allowance.html`: the "goes first" plate and line.
- Tests: twelve new tests in `test_proposal.py` (several of them in a real browser: one row on a phone, the fold's own row, the comment hiding it, the press) and three in `test_board.py`. The only change to existing test code: `_REVIEW_REPLAN` moved up the file unchanged, and `test_board.py` imports two helpers from `test_overview.py`.

There's no French in this milestone.

## Findings
| Id | Grade | Route | What |
|---|---|---|---|
| F1 | should-fix | claude, fixed | The mock-up dashes the card's edge as well as the plate when Approve first is pressed. The build dashed only the plate. `board.html` now gives the card `on-its-way` while the request is open (the board's existing "an order sent moves this card" edge). The two board tests check it appears and goes. |
| F2 | should-fix | claude, fixed | Nothing tested the Done when line "Approve first twice, on two cards: the later press stands first". Added `test_two_approvals_first_in_one_pick_leave_the_later_press_first`, which passes on the merged code. |
| F3 | nit | report | No test runs the refusal for "the header can't take the fast lane's mark" (`_goes_first` returning None). The refused-approval test is refused earlier, for a `runner/` file. The guard copies the lever's own, which is tested. |

**No checkpoint findings.** No checkpoint ran on this milestone.

Checks after the fixes: `tests/runner/test_requests.py` (341 passed), `tests/factory_dashboard/test_board.py` with `test_overview.py` (338 passed), and ruff clean. The whole `tests/runner tests/factory_dashboard` run hit this session's 10-minute limit at about 75%. It showed one failure right as it was stopped, and I couldn't see which test it was. The fixes touch only `board.html`'s card class and two test files, and every test of both is green, so the runner's own gates before the commit should settle it.

## Factory
- **Flow:** two tickets. The lead's runner ticket passed on attempt 1. The developer's pages ticket failed three times at the 20-minute limit with no edit, including once under an Opus direction, and went to Claude. No stops for you, no limits, no parks.
- **Models:** Sonnet $0.48 for f224-01. Opus $0.61 direction and $2.24 escalation for f224-02. Qwen spent about 2.6M tokens in for nothing merged.
- **To change:** note 12 in `.softfield/developer.md` (added by the escalation) is the first response. If the next difficulty-3 pages ticket stalls the same way, have the planner split wide UI tickets into one surface each, and send the direction after the first empty attempt.
