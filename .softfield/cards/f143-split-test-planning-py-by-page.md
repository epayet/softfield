# Milestone F143: Split the planning room's code and tests by page, so developers can take them

> **State:** done · **Priority:** 3 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-29. Base: git tag `f143-split-test-planning-py-by-page-start`. Report: [`.softfield/reviews/f143-split-test-planning-py-by-page.md`](../reviews/f143-split-test-planning-py-by-page.md).
> Planted by the owner on 2026-10-16.

## Notes
From docs/backlog.md (f84-review), 2026-11-02: Three plans (F30, F172, F84) sent a developer a ticket the Known range in `runner/instructions/lead.md` said was the lead's; the rule is prose the planner doesn't always read. Fix: once F143 lands its D6 rule (f143-05), make it a `check-tickets` check: a developer ticket whose `files:` span two pages' modules under `factory_dashboard/`, or a protected path, fails with "the lead's (lead.md, Known range)". Stays: waits for f143-05, which rewrites the rule the check would encode.

Split test_planning.py by page (desk, thread, proposals, plant), so the local developer can take planning-page tickets again instead of the lead. Open questions: one file per page or per feature? Does the split need its own ticket before the 16 lead tickets run, or can it go after?

## Plan (lead, 2026-10-27)
- **Why:** `tests/factory_dashboard/test_planning.py` is 4,441 lines and `factory_dashboard/planning.py` 1,492. Since F14's rule (`runner/instructions/lead.md`, Known range) every ticket that adds to that test file is the lead's; F13, F14, F30, F109 and F172 each lost three or more developer attempts to reading it with no edit. Since 2026-10-14, directions and escalations on planning tickets cost $12.83.
- **The layout gate sets the cut** (`layout_problems` in `runner/gates.py`): each test file in `tests/factory_dashboard/` is `test_<module>.py` for a module that exists. So a page's tests need a page's module: the code is split with them. No gate or rule changes.
- **Per page first, then per feature where a page is still too big:** three pages (desk, thread, proposal review), each with its own template already, plus two features big enough to stand alone: the Coming side of the desk (the Plant box, Coming, Didn't go through) and merge links.
- **The order:** the split goes before the planning-page tickets. 32 ready tickets name `planning.py` or `test_planning.py` (20 the lead's, 12 the developer's); the split helps only what runs after it. Each move points the tickets it would break at the new files in the same commit, or pre-flight would escalate them at their pick.
- Tickets, each waiting for the one before: `f143-01-proposal-page-own-module`, `f143-02-merges-own-module`, `f143-03-thread-page-own-module`, `f143-04-coming-own-module` (all lead, move only), then `f143-05-replan-routes-planning-tickets` (lead: re-routes the ready tickets that are the lead's only for F14's rule, and rewrites the rule).
- No mock-up: nothing on screen changes.

## Decisions
- **D1: five modules and five test files, flat in the same folders:**
  ```
  factory_dashboard/
    planning.py   desk: GET /planning, the groups, the tiles, Blocked, Archived   ← tests/factory_dashboard/test_planning.py
    coming.py     Coming, a waiting plant's edit and cancel, Didn't go through    ← tests/factory_dashboard/test_coming.py
    thread.py     GET /planning/{thread}: messages, standing, sign off, lever, note ← tests/factory_dashboard/test_thread.py
    merges.py     merge links, merged-on, a message's paths as links               ← tests/factory_dashboard/test_merges.py
    proposal.py   GET /planning/{thread}/proposals/{id}, the mock-up route, plan changes ← tests/factory_dashboard/test_proposal.py
  ```
  Templates stay as they are (`planning.html`, `thread.html`, `proposal.html`). Target: no test file over 1,500 lines, no module over 600.
- **D2: move only.** No behaviour, route, template, name or test body changes; every test keeps its name and passes unchanged. A test goes with the module whose function or route it exercises; a browser test of the Plant box goes to `test_coming.py`.
- **D3: shared test helpers stay in `test_planning.py`** and are imported from it, as `tests/factory_dashboard/test_board.py` already imports `_open`. Fixtures shared by more than one file (`planning`, `checkout`) move to `tests/factory_dashboard/conftest.py`. Nothing else grows conftest.
- **D4: imports run one way:** `thread.py` and `proposal.py` may import `planning.py`, `coming.py` and `merges.py`; `planning.py` imports `coming.py`; `coming.py` and `merges.py` import neither page. Other modules' imports (`app.py`, `milestones.py`, `projects.py`, `board.py`, `overview.py`, `tests/factory_dashboard/test_overview.py`) point at the new homes; the routers are each included in `app.py`.
- **D5: each move points the tickets it breaks.** A ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` that names a moved `def`, `class` or test beside its old path names the new path, in `files:`, `tests:` and Context, in the same commit. The same for the worked examples in `.softfield/developer.md`.
- **D6: the routing rule after the split** (f143-05): a planning-page ticket goes to the developer when it touches one page's module, its test file and its template (and the CSS); one that spans two pages' modules, or a protected path, stays the lead's.

## Replan (f143-05, 2026-10-28)
The rule is rewritten in `runner/instructions/lead.md` (F14's and F172's entries) and `runner/instructions/task-writing.md` (the finding rule). Ready tickets with `agent: lead` that touched the planning room, one line each:
- **Re-routed to the developer** (`agent: lead` removed; one page's module, its test file and its template, difficulty 4 or less, not protected):
  - `f63-01-desk-order`: `planning.py`, `planning.html`, `test_planning.py`; its card (F63) already calls it a developer ticket.
  - `f26-02-group-counts`: `planning.html` and `test_planning.py` only.
  - `f73-01-set-aside-list`: `planning.py`, `planning.html`, `test_planning.py`; difficulty 4, follows `archived` as its example.
  - `f108-01-desk-says-when`: `planning.py` and `test_planning.py` only; difficulty 2.
  - `f32-01-lead-window-resets`: `planning.html` and `test_planning.py` only; it was the lead's for F14's rule alone (its stop was a red main).
  - `f65-03-round-on-page`: `thread.py`, `thread.html`, `test_thread.py`; its card (F65) already calls it a developer ticket.
  - `f73-02-set-aside-button`: `proposal.py`, `proposal.html`, `test_proposal.py`; its Context named `planning.py` for the page function, which is `proposal_review` in `proposal.py` since f143-01: fixed.
  - `f42-01-review-page-room`: `proposal.html`, the CSS and the review page's tests; its phone test is `test_on_a_phone_one_point_shows_at_a_time` in `tests/factory_dashboard/test_thread.py` now, so Context and `tests:` name that file instead of `test_planning.py`.
- **Left with the lead, fits D6's lead side or has another reason:**
  - `f33-02-now-estimate`: spans `overview.py` and `coming.py` (moves `_typical` between them). Its `tests:` named `test_planning.py` for the next-reply estimate, which is in `test_coming.py`: fixed.
  - `f74-01-one-box-per-conversation`: spans `planning.py` and `coming.py`.
  - `f75-01-archiving-on-approval`: spans four page modules.
  - `f100-01-proposals-being-revised`: spans `planning.py`, `thread.py` and the proposal page's template.
  - `f112-01-replan-in-plain-words`: spans `proposal.py`, `thread.py` and `planning.py`.
  - `f164-03-idea-plates-with-plant`: spans `thread.py` and `milestones.py`.
  - `f67-02-key-points-by-kind`: one page's files, but difficulty 5.
  - `f71-03-browser-tests-on-a-fake-clock`: tests only across four test files, difficulty 5.
  - `f152-02-every-mockup-is-listed`: `runner/` (protected), not a dashboard ticket; its `_MOCKUP_RE` pointer to `planning.py` is still right.
- **Checked against the moved code:** the `def` names in these tickets' Contexts (`_answers_wanted`, `_open_proposals` in `planning.py`; `_acted_on`, `_held`, `_next_reply`, `_typical` in `coming.py`; `_review`, `_proposals`, `_standing` in `thread.py`; `proposal_review`, `_plan_changes`, `mockup_file` in `proposal.py`) sit where the tickets say, except the two fixed above. `f81-04-desk-in-classes` and `f89-02-meters-say-when-read` already go to the developer.
