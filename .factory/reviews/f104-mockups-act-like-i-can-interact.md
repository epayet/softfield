# Review: F104, a mock-up answers in the review page's frame

- **Status:** done, signed off by the owner on 2026-10-13.

## Sign-off sheet

**Expected:** your note was "Mockups act like I can interact with but I can't, f54 is blocked because of that". A mock-up should work where you read it: in the review page's frame its buttons, tabs and switches answer, and nothing it runs can act as the dashboard.
**Done when:** on a wide screen, F54's mock-up answers inside the review page ("A · stays in place", then ↑ on a row). On a phone it opens full screen from its link and answers the same way: that half waits for f42-01, which isn't built yet.

### 1. What changed
- A mock-up's buttons, tabs and switches now answer inside the review page. Before, the frame turned its scripts off, so F54's mock-up showed its tabs, did nothing when pressed, and its queue was empty.
- The frame lets scripts run and nothing else. A mock-up still can't read the page around it, press Approve, or send a request as you: the browser treats it as a stranger, and the dashboard refuses a stranger's requests.
- New in this review: the lead's planning brief now says what the frame still refuses (saved state, pop-up dialogs, forms, requests to the dashboard, links to a new tab), so a new mock-up isn't drawn with something that would go dead in the frame.

### 2. How to test it yourself
1. On a computer (a wide screen), open the planning room, F54's card, and its mock-up proposal.
2. In the frame, press "A · stays in place": the tab changes.
3. Press ↑ on a row: the row answers.
4. Press "Refresh", "Reload" and "Runner's next pick": each answers.
5. On a phone, the frame is the same small box as before, and it answers too. Full screen on a phone comes with f42-01.

I didn't open F54's mock-up in a browser myself: a review job has none. A test does it in Chromium with a small mock-up whose script writes into its page, and I read F54's mock-up for anything the frame refuses and found nothing.

### 3. Left for later
- **f42-01** (ready, a developer ticket): the "Open the mock-up" link, a taller frame, and on a phone the link in place of the frame. It is the second half of F104's Done when. Its ticket already says to keep the frame's setting and its test.
- **bug-01** (ready, new): a review reads its own milestone's commits. This one was handed 158 files.
- Backlog (F3): a mock-up split into several files would lose its stylesheet. The brief asks for one file, so nothing breaks today.

### 4. Decisions waiting for you
None. The one security decision here (D1: scripts, and nothing else) was taken with you in the session of 2026-10-13.

### 5. How the work went
- 2026-10-10: planted, answered from the code and planned the same day. Its ticket was set to wait for f42-01, since both change the same lines.
- 2026-10-13 11:30 ([session](../sessions/2026-10-13-1130-lead.md)): your terminal session. f104-01 built by the lead, test first, ahead of f42-01: one attribute and one Chromium test, in the commit that also fixed F107's causes. No local tokens.
- 2026-10-13: this review, round 1. One small fix by the review, one bug ticket, one backlog line.
- Lessons:
  - A one-line fix that unblocked you waited three days behind a ticket nothing moved, because the two shared lines. When a fix unblocks the owner, it goes first and the other ticket is told what it will find. That is what the session did; the plan should have.
  - Letting scripts run was half the fix. A mock-up that saves its state or opens a dialog would still go dead in the frame, with the same symptom. The brief now lists what the frame refuses.
  - A ticket built in a terminal session carries no mark the runner can find, so the review's start fell back to the day the card was planted (bug-01).

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Queue f42-01 soon: on a phone the mock-up is still a 480-pixel box, and you read these on a phone.
  - bug-01 before the next reviews of terminal-session work (F49 and F109 will meet the same thing).
  - A mock-up could say so itself when something is refused, instead of going quiet. Not worth a ticket until one does go quiet again.

### 7. What clogged the factory line
- **Three days between the plan and the fix** (2026-10-10 to 2026-10-13): f104-01 waited for f42-01, a developer ticket that itself waited for f12-03 and its turn. No agent worked on either. What unclogs it: don't make a fix that unblocks you depend on a ticket for sharing its lines; order them the other way.
- **18 minutes of checks for one attribute** (the session's own measure): `check-all` with the browser tests. What unclogs it: F71's slow-tests study (f71-02, ready).
- **The review:** one run of the three test folders, 3 min 39, and a 7,600-line diff to sort before finding the 36 lines that were F104's. What unclogs it: bug-01.
- I couldn't read hours from the metrics database in this job (a headless review has no query command); the figures are from the session report and git. The fix is in the backlog (f53-review: a "where the hours went" block in `runner report`).

## What was built
- **The frame** (`factory_dashboard/templates/proposal.html`): `sandbox` became `sandbox="allow-scripts"`, the same words as the mock-up route's own `Content-Security-Policy`.
- **Tests** (`tests/factory_dashboard/test_planning.py`):
  - new, in Chromium at 1024 px: a mock-up whose script writes into its page shows "alive null refused" inside the review page: the script ran, its origin is `null`, and reading `parent.document` threw. The frame's attribute is exactly `allow-scripts`.
  - changed: the route test's pattern for the frame follows the new attribute.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The planner's brief asked for "self-contained HTML" and said nothing of the frame. A mock-up using `localStorage`, `alert` or `confirm`, a form, a request to the dashboard or a link to a new tab would go dead there, some of them stopping the whole script: the owner's complaint again | Fixed: one sentence in `PLANNER` (`runner/prompts.py`), checked in `tests/runner/test_prompts.py` |
| F2 | nit | backlog | Round 1 was told to read `git diff f104-…-start..main`: 158 files, 7,600 lines. f104-01 was committed in a terminal session with no `Task:` trailer, so `_plan_commit` (`runner/milestone.py`) tagged the commit that planted the card. Second time in a day a review read other milestones' work (f79-F3) | A nit for F104 (nothing it built is wrong), but it recurs, so it is a ticket and not a backlog line: `tasks/ready/bug-01-review-reads-its-own-commits.md`, priority 20, a lead ticket (protected code), which replaces f79-F3 in the backlog |
| F3 | nit | backlog | `mockup_file` answers every file as `text/html`, so a mock-up in several files loses its stylesheet | `docs/backlog.md`; the brief now asks for one file |

Read and found sound, no finding:
- **D1 holds.** Without `allow-same-origin` the frame's origin is opaque: no cookies, no storage, no reading of the parent. The dashboard's only writing route is `POST /requests`, which wants htmx's header and a same-host `Origin`; a sandboxed frame sends `Origin: null`, refused (`tests/factory_dashboard/test_requests.py`, the "a sandboxed frame or a file" case). No `allow-forms`, `allow-popups`, `allow-top-navigation` or `allow-modals`.
- **The test can fail.** On a bare `sandbox` the script doesn't run and the wait for "alive" times out; with `allow-same-origin` the text would be the dashboard's origin and its title; any added token fails the exact attribute check.
- **F54's mock-up** (`docs/milestones/f54-mockup/moves.html` on its plan branch): one file, no storage, dialog, form, request or link, so it works in the frame as it is.
- **D3 reversed** (f104-01 before f42-01): the milestone doc says so, and f42-01's ticket was updated to keep the attribute and the test.

Edited existing tests: one, `test_the_mockup_route_serves_the_plan_branchs_mockup_and_nothing_else`, whose frame pattern follows the attribute. Not weakened: it still checks the route, its `Content-Security-Policy` and the refused paths. The review added three assertions to `test_the_planner_prompt_names_the_block_the_branch_and_the_approval_rule`.

Not reviewed here: the rest of the 7,600 lines, which are F5's, F21's, F31's, F48's, F49's, F53's, F79's and F109's tickets and the planning of a dozen cards. Each has, or will have, its own review; F31, F48, F53 and F79 already do. I read only what F104 built and what it leans on.

No checkpoint ran (a lead ticket in a terminal session), so there are no checkpoint findings to judge. French: nothing to check, no user-facing string and no `coucou/locale/` file changed. Screenshots: no browser in this job. After the fix, `uv run pytest -q tests/unit tests/integration tests/runner` gave 1818 passed, 1 skipped; the two mock-up tests in `tests/factory_dashboard/test_planning.py` pass, the Chromium one included; ruff is clean on the two edited files.

Score: 9/10. The smallest change that does it, the security reasoning written down and checked where only a browser can check it. It lost a point for stopping at the attribute: nothing told the next mock-up's author what the frame refuses.

Stop reason: none; nothing is left for a round 2. bug-01 is a bug ticket, outside this milestone, and doesn't hold the sign-off.

## Factory
- **The flow:** no runner job built this. Planned by a planner job on 2026-10-10, built by the lead in your terminal session three days later. No stop, park or limit on F104 itself.
- **Models:** Claude Opus only; see the numbers below. No developer work, so "Known range" in `docs/agents/lead.md` has nothing new.
- **What to change:**
  - A review reads its own commits (F2, bug-01).
  - A commit that builds a ticket in a terminal session names the ticket in its subject (part of bug-01), so the runner can find it.
  - A lead ticket gets no checkpoint, so its review is its only reader (F41, F53, F55 and F79 said the same). Here that was enough.

## Workflow observations
- `runner report` counts only the runner's merges, so this milestone will read as nothing merged (backlog, f41-F3). Its one ticket is in `tasks/done/` with the session's commit named in the milestone doc.
- The ticket's `depends_on` still names f42-01 though it was built first; harmless in `tasks/done/`, and the milestone doc's ticket table says what happened.

<!-- runner report -->
<!-- /runner report -->
