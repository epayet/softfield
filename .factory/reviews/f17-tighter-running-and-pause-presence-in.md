# Review: F17, a dot and a sign in the top bar

- **Status:** round 2 done (the round 1 fixes hold), ready for your sign-off.

## Sign-off sheet

**Expected:** your note was "I don't need to see the name of the task, just a pointer that tells me if it's doing a job or not… orange or blue… the pause button should be just a sign". The top bar's status is a dot (orange: the lead on a job; blue: a developer; grey: no job; an orange ring while waiting for Claude; a grey ring when stopped), and Pause or Resume is a sign, ⏸ or ▶. On a phone the dot and the sign sit on the brand's row and the words show on a tap; on a wide screen the words stay beside the dot.
**Done when:** at 390 px the brand, the dot, the sign and the project share one row, the dot and the sign are 44 px thumb targets, and no words show until the dot is tapped; at 1024 px the words are beside the dot; tapping ⏸ still shows "Pausing after …" with the dashed orange edge at once.

### 1. What changed
- The top bar's status is now a dot and a sign, as in the mock-up ([`f17-mockup/top-bar.html`](../cards/f17-mockup/top-bar.html)). The dot breathes slowly while a job runs (not if your phone asks for reduced motion).
- On a phone the whole status moved up beside "software-factory": the bar is one row shorter. Tap the dot to read what the factory does; tap it again to hide the words. They stay open through the page's refresh.
- On a laptop the words are where they were, now with the dot before them and ⏸ or ▶ after.
- When you tap ⏸ or ▶, the dashed orange edge now goes round the whole status, dot and words.
- Also in this milestone, from the same day's terminal session:
  - a developer attempt is now stopped for "no edit" after 20 minutes, not 10 (F93);
  - Claude's jobs get 75 minutes, not 45;
  - a runner stopped while it checks or merges the lead's work no longer leaves that work loose on main and refuses to start: it puts the work on a branch and carries on next time (F71 D8). The review fixed one more case of it (below).

### 2. How to test it yourself
1. On your phone, open the dashboard. The top row reads: software-factory, a dot, ⏸, the project. No second row for the status.
2. While a review or the lead's ticket runs, the dot is orange; while the developer works on a ticket, blue. Between jobs or idle, grey.
3. Tap the dot: a small box under it says what is running ("Running: softfield · review, job 986" right now). Wait for the page to refresh (a few seconds): it stays. Tap the dot again: it goes.
4. Tap ⏸: the status gets a dashed orange edge at once and the box says "Pausing after …"; ⏸ disappears, then ▶ comes back on the next refresh. Tap ▶ to resume.
5. On your laptop, the words show beside the dot without a tap.

### 3. Left for later
Three small notes in `docs/backlog.md`, none visible to you today:
- the bar's old colour names are still computed though nothing shows them (tidy-up);
- if two projects ever run at once, the dot could show grey for one while the other works (only one runner runs today);
- a stop in the few seconds between merging a lead ticket and filing it would run the ticket again.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-07: planted by you and planned in the planning room, one developer ticket (f17-01, difficulty 4) with a mock-up.
- 2026-10-10 ([session report](../sessions/2026-10-10-0854.md)): the developer (Qwen) tried three times, 12.7M tokens. Two timed out and one stopped with no edit; the failures were mostly a test file another review had left on main. The escalation sent it back, "your branch holds nearly all of it", behind the ticket that removed that file.
- 2026-10-16, 07:10: three more attempts, 588k tokens, each stopped after 10 minutes of reading. The branch the ticket described no longer held the work. The lead's escalation built it, decided "implemented", and was then cut off at its 45-minute limit while it waited for its second check-all. The runner was then stopped during its own check-all and wouldn't start again, so the work was finished and committed in a terminal session (09:13), with the runner fixes above.
- 2026-10-16: this review, round 1. Two fixes by the review, three backlog lines, no ticket.
- 2026-10-16: round 2 re-read the two fixes: both hold, nothing new.
- Lessons:
  - **A requeue's "the branch so far" goes stale.** Six days later the branch was gone and the ticket still told the developer not to start again. Written into "Known range" (`docs/agents/lead.md`): check `git diff main...task/<id>` before trusting it.
  - **The runner's own steps after a Claude job are part of the job.** A stop there lost track of finished work. They now count as the job in flight (F71 D8); the review closed the parked case.
  - **The top bar is the lead's work** by F14's rule (its script plus browser tests in `test_app.py`); it took six developer attempts to learn it again.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - A requeue that tells the developer what its branch holds could be checked by the runner, not just remembered by the lead. Text ready to paste in the Plant box: "When a ticket comes back from escalated after days, the runner checks that the branch its ticket describes still differs from main, and sends it to the lead if not. Open questions: check at requeue or at pick? Drop the 'branch so far' section, or route the ticket to the lead?"
  - F144 and F145 (a review opens the real page first) are already planted; this review did it with `softfield look page` and it confirmed the bar.

### 7. What clogged the factory line
- **About three hours of developer attempts on a ticket that was the lead's by an existing rule** (three on 2026-10-10, two of them run to their time limit; three 10-minute stops on 2026-10-16). What unclogs it: the routing rule applied to waiting tickets (F30's review moved 16; this one had been requeued before that rule).
- **Six days between the requeue and the next try**, waiting behind f12-03 and higher priorities.
- **A stopped runner that wouldn't restart** (2026-10-16, from the escalation's cut-off until the terminal session's commit at 09:13): fixed by F71 D8 and this review's F1.
- The minutes come from the session reports and the ticket's footers; the per-wait hours from the metrics database are in the runner's block below.

## What was built
- **`Status.dot`** (`factory_dashboard/app.py`): `lead` or `developer` for the first live job (the one the words name), `waiting`, `stopped`, else `idle`. While paused only the planner counts (`lead`, else `idle`). Any role outside `DEVELOPER_ROLES` is `lead`.
- **`bar_status.html`**: the dot is a button whose `aria-label` and `title` are the words; the words stay in the `role="status"` span; the sign is ⏸ "Pause after this job" or ▶ "Resume" by `aria-label`. The dashed edge is on `#factory-status.asked`.
- **`dashboard.css`**: the dot's colours from the tokens (`--opus`, `--dev`, the floor's developer bay, `--muted`), glow by `color-mix` (no raw colours), the breath only under `prefers-reduced-motion: no-preference`; on a phone the status takes the brand's row, 44 px targets, the words as a box under the dot on a tap.
- **`base.html`**: one `failed` handler for both htmx errors, and a click on the dot toggles `show-words` on `.bar-top`, which the polls don't swap.
- **Runner (F71 D8, F93):** `_settling` keeps a lead ticket or escalation in flight through check-all, commits and the merge; `_recover` keeps an off-main branch even with nothing new to commit; a resumed escalation isn't counted again; an escalation with no decision keeps its work on `escalation/<id>`; a timed-out session keeps its session id (`stream_session`) and says "cut off at its time limit"; `NO_EDIT_AFTER` is 20 minutes and the stop's words come from it.
- **By the review:** F1 and F2 below.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | An escalation parked at a usage limit after writing its decision lost that decision when it resumed: the new "resuming" excludes a parked one, so `decision.json` was deleted, and the resumed session could end with no decision, blocked | Fixed in `handle_escalation` (`runner/loop.py`): removed only when there is no earlier run of this escalation. New `test_an_escalation_parked_after_its_decision_keeps_it_for_the_resume`, which fails without it |
| F2 | nit | claude | Recovering a lead ticket stopped during its check-all said "it had changed nothing", though its branch held the whole ticket | Fixed in `_recover`; one assertion added to `test_a_lead_ticket_stopped_during_its_check_all_keeps_its_branch` |
| F3 | nit | backlog | `Status.tone` still hands out good/warn/serious, unstyled since the words lost their colour | `docs/backlog.md` |
| F4 | nit | backlog | With two live projects, a grey "picking the next ticket" ranks equal to a running job in `factory_wide_status` | `docs/backlog.md` |
| F5 | nit | backlog | A stop between a lead ticket's squash merge and its `done/` commit re-runs a merged ticket | `docs/backlog.md` |

Read and found sound, no finding:
- **The dot follows the words.** The same first live job feeds "Running: …", "Pausing after …" and the dot; `_lead_ticket` puts the lead ticket on a run of its own, so the test no longer passes on a developer job left live beside it (the branch's old special case is gone).
- **`--dev`, not `--copilot`.** The ticket said `--copilot`; the lead used `--dev`, which is the floor's developer bay (`.floor .developers`) and what the mock-up's text asks for ("the developer bay's blue"). Right call.
- **A checkpoint stand-in** (a non-Claude checkpoint) shows orange: it does the lead's role. Fits the card's "any Claude job" closely enough; noted, no change.
- **`_settling` has no `finally`** on purpose: a stop must leave the job in flight for `_recover`.
- **`resuming`** counts an interrupted escalation once, and a parked one is still re-counted on resume as before (its count was taken back when it parked).

Edited existing tests: in `test_app.py`, the parametrised top-bar test gained the dot per state (words unchanged, rows reordered, one new `lead-ticket` row); `_status` now finds the sign by `aria-label` and checks it shows only ⏸ or ▶; the colour test now checks the dot's tokens instead of the old pill's; the three stale-poll and refused-post browser tests find the sign by its name and build their fragments with the real partial (`_bar`) instead of pasted HTML, a real improvement; two of them also assert the dashed edge. `test_requests.py`'s `_now_pause` reads the new span. In `test_local_model.py`, the two no-edit tests moved from 10 to 20 minutes with longer frames and an extra tick check (19.5 is passed through). None was loosened.

No checkpoint ran on this milestone (the ticket was finished by the lead), so there is no checkpoint finding to judge. French: nothing to check, no `coucou/locale/` file changed. Screenshots: no browser in this job; the live top bar was read as text with `softfield look page /tickets` ("Running: softfield · review, job 986 ⏸"). After the fixes: `uv run pytest -q tests/runner tests/factory_dashboard` gave 2314 passed; ruff and mypy are clean on `runner`.

Score: 8/10. The bar matches the mock-up and your notes, with careful tests (sizes, rows by their middles, the tap surviving a poll, reduced motion, tokens only). The runner fixes close a real stall. It loses points for six wasted developer attempts on a ticket that was the lead's, and for F1, a gap in the same day's recovery work.

Stop reason: none; nothing is left for a round 2.

### Round 2
Only the review's own fixes changed since round 1 (`git diff 16b7d2d^..main`: `runner/loop.py`, one test added, one assertion added, three backlog lines). Both hold:
- **F1:** `handle_escalation` now removes `decision.json` only when `earlier is None`, the same rule `run_claude` applies to a job's process note. A parked escalation keeps the decision it wrote before the limit; a new escalation after a finished one still starts clean; one parked before it wrote anything had its file removed when it first started. The new test runs the park and the resume through `run_session` and checks the ticket reaches `done/`.
- **F2:** `kept` follows `where`, so the line names the branch whenever the recovery keeps one; the assertion pins the words.

No new finding, no ticket, F3–F5 stay in the backlog. `uv run pytest -q tests/runner tests/factory_dashboard`: 2314 passed. Score unchanged: 8/10.

## Factory
- **The flow:** one developer ticket, six attempts over two sessions, two escalations (one requeue, one implemented and cut off at its limit), then a stopped runner that wouldn't restart until a terminal session finished the work. No park for a limit; one stop for the owner's terminal session.
- **Models:** Qwen (qwen3.6-35b-a3b) on all six attempts, about 13.3M tokens; Claude Opus for the directions, both escalations, the terminal session and this review. Dollars in the numbers below.
- **What to change:**
  - Check a requeued ticket's "branch so far" against the branch before it runs again (written in "Known range"; planted-card text in item 6 for a runner check).
  - The 75-minute limit for Claude's jobs is now above the review's 60: if a review is cut off, raise `review` too.

## Workflow observations
- The 07:10 run has no session report: it was stopped during check-all and the runner never reached its end. The terminal session's commits carry its story; this review is its narrative.
- Round 1 read the terminal session's runner work as part of the milestone (the known `bug-01-review-reads-its-own-commits`); here that was useful, since the runner fixes were caused by this milestone's ticket.

<!-- runner report -->
<!-- /runner report -->
