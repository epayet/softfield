# Review: F143, the planning room's code and tests split by page

## Sign-off sheet

### 1. What changed
Nothing you can see: every page of the planning room looks and works as before. Behind it, the 4,441-line test file and the 1,492-line page module are now five of each, one per page or feature: the desk (`planning.py`), Coming and Didn't go through (`coming.py`), a card's thread (`thread.py`), merge links (`merges.py`) and a proposal's review page (`proposal.py`), each with its own test file. The point is the queue: eight ready tickets that waited for Claude only because of the big test file now go to the local developer again, which costs nothing per ticket.

### 2. How to test it yourself
1. On the phone, open Planning: the desk shows the same groups, Coming and the Plant box as yesterday. Plant a short idea: it shows at once, dashed orange.
2. Open a card's thread: messages, Send, the reserve lever and (on a finished card) Sign off are where they were.
3. Open a proposal from the desk: the review page, its key points, comments and the mock-up still open; on the phone, ◀ ▶ step through the points.
4. Open a merged card: the "merged into" links still go both ways.
5. Over the next sessions, watch the board: tickets such as `f63-01-desk-order` and `f73-01-set-aside-list` should now be taken by the local developer, not Claude.

### 3. Left for later
- Nothing new from this card. The first developer runs on the re-routed tickets are the real test of the split (see 6).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-26 22:52 ([session](../sessions/2026-10-26-2252.md)): the planner job was parked (Claude was limited); 2026-10-27 09:09, planned by the lead (Claude Opus), $2.36.
- 2026-10-28 13:41 ([session](../sessions/2026-10-28-1341.md)): all five tickets built by the lead (Claude Sonnet), each first time, 6 to 19 minutes, about $4.66 together; 0 local tokens on this card. Between `f143-03` (14:28) and `f143-04` (19:03) the line ran two F81 developer tickets.
- Lessons:
  - A move done by the lead in small steps, each pointing the tickets it breaks at the new files in the same commit (D5), left no ticket broken: every `def` and test the ready tickets name is where they say, and `softfield check-tickets` passes on all eight re-routed ones.
  - The move kept every test: 200 test functions before, 200 after, and no test body changed.
  - A routing rule lives in several places. f143-05 rewrote two of them and missed a third (F84's line in `lead.md`), fixed in this review.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** watch the first developer runs on the re-routed tickets (`f63-01`, `f26-02`, `f73-01`, `f108-01`, `f32-01`, `f65-03`, `f73-02`, `f42-01`). If they still read for 20 minutes without an edit, the problem was never only the file's size, and the next step is shorter tickets with line numbers, not more splitting. The F84 idea also still stands: a check that refuses a developer ticket spanning two pages' modules. Text ready to paste in the Plant box: "check-tickets refuses a developer ticket whose files: span two planning pages' modules (planning, coming, thread, merges, proposal): F143 D6's rule as a check, so a planner can't route one wrong again."

### 7. What clogged the factory line
- **4 h 35 min of waiting for `f143-04`** (14:28 to 19:03): the runner takes developer tickets before lead tickets, so the F81 tickets ran first. In that time the local developer made three attempts with no edit (60 min) and two timeouts (2 h 33 min) on `f81-05` and `f81-08`, which needed two directions and an escalation. Nothing here held F143 itself up: it just waited its turn on a one-worker line. What would unclog it is a second worker (your priority 7, "faster, parallel workers"), so a lead ticket doesn't wait behind a slow local one.
- No limit waits, no stops for you, no failed attempts on this card.

## What was built
- `factory_dashboard/proposal.py` (156 lines): the review page `GET /planning/{thread}/proposals/{id}` and the mock-up route, with `tests/factory_dashboard/test_proposal.py` (21 tests).
- `factory_dashboard/merges.py` (187 lines): merge links, merged-on and a message's paths as links, with `test_merges.py` (19 tests).
- `factory_dashboard/thread.py` (459 lines): `GET /planning/{thread}`, its proposals' standing, the review, Sign off and the lever, with `test_thread.py` (55 tests).
- `factory_dashboard/coming.py` (548 lines): Coming, a waiting plant's edit and cancel, Didn't go through, the reply line and the desk's item classes, with `test_coming.py` (56 tests, the Plant box's browser tests among them).
- `factory_dashboard/planning.py` is now the desk alone (478 lines), `test_planning.py` 1,389 lines (49 tests) and the shared helpers (D3). The `planning` and `checkout` fixtures moved to `tests/factory_dashboard/conftest.py`.
- The routers are included in `app.py`; `milestones.py`, `overview.py` and `test_overview.py` import from the new homes.
- f143-05: the routing rule (D6) in `docs/agents/lead.md` (F14, F172) and `docs/task-writing.md`; eight ready tickets lost `agent: lead`, and three had their pointers fixed (`f33-02`, `f42-01`, `f73-02`). The card's "Replan" lists each ticket and why it moved or stayed.

Tests: no existing test was changed beyond its imports. The four `test_overview.py` tests that read `_card_titles` import it from `coming.py`. Every target of D1 is met: no module over 600 lines, no test file over 1,500.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | `lead.md`'s F84 entry still asked for a check sending any `test_planning.py` ticket to the lead, against D6 | Fixed: the entry says the rule changed with F143 D6 and what a check would refuse now |
| F2 | nit | claude | `developer.md` said the `checkout` fixture sits beside `_posts`; it moved to `conftest.py` in f143-01 | Fixed: the note names `conftest.py` |
| F3 | nit | claude | An orphaned comment above `_ADR_NUMBER` in `planning.py`, older than the split, carried over by the move | Removed |

No checkpoint ran (five lead tickets), so there are no checkpoint verdicts. Score: 9/10. A clean move, made in safe steps and checked against the queue ticket by ticket. The only slip was one routing line in `lead.md` left with the old rule.

Checked and fine: imports run one way with no cycle. `coming.py` and `merges.py` import no page; `planning.py` imports `coming` and `merges`; `thread.py` imports those and `planning`; `proposal.py` imports `thread.py` too, which D4 doesn't list but which closes no loop, since `thread.py` imports nothing from `proposal.py`. The four routes don't overlap whatever order the routers are included in. No runner code reads `test_planning.py` or `planning.py` for routing, so the re-routed tickets aren't sent back. Every `def` and test that a ready or later ticket names beside `planning.py` or `test_planning.py` is still there. The test that `f42-01` reads, `test_on_a_phone_one_point_shows_at_a_time`, is parametrised over the thread and the review page, so `test_thread.py` is a fair home. Ruff passes. The whole runner and dashboard suite ran past the 10-minute foreground limit and kept going in the background. It was stopped at its 20-minute limit at about 97%, with no failure before then (it ran with `-x`; the `E` printed after the kill is its teardown). The review's own fixes are one deleted comment and two lines of docs, so no test can change because of them.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing added. `tests/factory_dashboard/conftest.py` is 2,203 lines, most of them older than this card; D3 keeps it from growing (only the two shared fixtures joined it).

## Factory
- Flow: five lead tickets, each first time, no checkpoint (lead tickets), no stops for you, no limit waits, no parks. The card waited 4 h 35 min behind two F81 developer tickets.
- Models: Claude Opus $2.36 for the plan; Claude Sonnet $4.66 for the five tickets (moves of 600 to 1,700 lines each, $0.49 to $1.39). Local: nothing on this card.
- What to change: the split is only worth what the next developer runs show. Read the first three re-routed tickets' results at their checkpoints. If the local developer still stops with no edit on a ~1,200-line test file, write the findings into `docs/task-writing.md` (name the test to copy and its line) rather than splitting further.

<!-- runner report -->
<!-- /runner report -->
