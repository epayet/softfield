# Review: F72, a card that changes a page gets a Today / Proposed mock-up, unasked

- **Status:** done, signed off by the owner on 2026-10-13.

## Sign-off sheet

**Expected:** when you plant or write on a card that changes how a page looks, the lead's first reply carries a mock-up with Today and Proposed of the same page, beside the plan. You see the change before any ticket is queued, and the tickets point at that picture.
**Done when:** the planner's brief says when a mock-up is due, what it shows and that the tickets point at it; `lead.md` and `owner.md` say the same, so a terminal session does it too; the next frontend card planned after the merge gets a Today / Proposed mock-up without being asked.

### 1. What changed
- The planner's brief now tells the lead: a card that changes what a page shows or how it is laid out gets a mock-up without you asking, on the dashboard and in the app alike. Not for wording only, a bug that restores the intended look, or work with nothing on screen. When the lead skips one on a card with screen changes, it says why in a point, so you can ask for one.
- The mock-up is one file with a Today / Proposed switch at the top. Today is copied from the live page, Proposed outlines each change with a short note, and both use real values.
- The mock-up and the plan arrive in the same reply, one round fewer than "iterate the mock-up, then write the tickets". Each UI ticket names the mock-up as the picture to build.
- The same rule is in `docs/agents/lead.md` and `docs/agents/owner.md`, so a terminal session follows it too.
- Nothing on the dashboard itself changed. You will see it in the lead's next reply on a frontend card.
- The first two of the three Done-when lines are met. The third (the next frontend card gets one) can only be seen on that card: step 1 below.

### 2. How to test it yourself
1. In the planning room, plant a card that changes a page (for example "show the queue's length in the top bar") and wait for the lead's first reply. It should carry a mock-up proposal next to the plan. Open it: a Today / Proposed switch at the top, Today looking like the live page, each change in Proposed outlined with a note.
2. Open one of the plan's UI tickets from the same reply: its Context names the mock-up file.
3. Plant a wording-only card (for example "rename Overview to Home"). The reply should carry no mock-up, or a point saying why not.
4. For the format the lead is told to follow, open F94's mock-up from its card: it has the switch.

### 3. Left for later
- **The real after, at sign-off** (F72's "Later"): a screenshot of the built page next to the mock-up's Proposed, on the review page, to see whether the build matches the picture. It needs a headless browser in the runner. My recommendation: add it to `docs/roadmap.md` as an idea now, and plan it after F71 (slow tests), since it adds browser work to every frontend sign-off. Say no and I leave it out.
- No backlog line from this review.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-13 11:25 ([session](../sessions/2026-10-13-1125.md)): `f72-01-mockup-by-default` merged at its first attempt, a headless lead job (`runner/` is protected), 27 minutes. No local tokens. The runner stopped after it for a fresh process, as it does when `runner/` changes.
- 2026-10-13: this review, round 1. One small fix by the review, no ticket.
- Lessons:
  - Your preference took four days from planting (2026-10-09) to the brief, and two mock-ups in the new format were drawn in between (F94's with its plan on 2026-10-10, F15's in a terminal session on 2026-10-13). The format was tried before it became the rule, which is why the rule is concrete.
  - The plan named F17's mock-up as the example, and the brief copied it. F17's was drawn before the format existed and has no switch. An example named in a brief is checked against the sentence before it; the test now does that for this one.
  - 27 minutes for 62 lines of text: the gates, not the writing. Same as F79 this morning.

### 6. What next
- **Product:** on hold, as you asked. The rule covers the app's pages too, so the first product card with a screen change will get its Today / Proposed without more work.
- **Factory:**
  - Watch the next two or three frontend cards: does the mock-up come unasked, is Today really the live page, and does the lead say why when it skips one? If Today drifts from the live page, the fix is a ticket that renders Today from the real template instead of asking the lead to copy it.
  - On a wide screen the plan asks for Today and Proposed side by side; the two mock-ups in the new format (F94, F15) only switch. The brief asks for both. If the next one still only switches, either build it once as a template the lead copies, or drop "side by side" from the rule. I'd wait for one more mock-up before choosing.
  - F71 (slow tests) before more runner tickets: a change of words in a prompt shouldn't cost 27 minutes.

### 7. What clogged the factory line
- **F72 itself:** nothing. One attempt, no limit wait, no stop for you. Planted 2026-10-09 and built 2026-10-13: it waited its turn behind the planning-room work, your priority order.
- **Inside its 27 minutes:** probably mostly `check-all` with the browser tests (18 minutes when a terminal session measured it this morning); not measured for this job. What would unclog it: F71.
- **The review:** one run of the three test folders, 3 min 43. The diff was the milestone's own 62 lines this time.
- I couldn't read hours from the metrics database in this job (a headless review has no query command); the figures are from the session report. The fix is already in the backlog (f53-review: a "where the hours went" block in `runner report`).

## What was built
- **The brief** (`runner/prompts.py`): one paragraph in `PLANNER`, after the one that says where drafts go, covering D1 (when, the exceptions, "say why in a point"), D2 (one file, the switch, Today copied, changes marked, real values) and D3 (same reply, tickets name the file, tickets revised with the mock-up). `PLANNER_GENERAL` is unchanged: that thread drafts nothing.
- **The docs:** one line in `docs/agents/lead.md`'s Planning room; `docs/agents/owner.md`'s "Mock-ups before UI tickets" widened from "a new view" to D1 and dated.
- **The test** (`tests/runner/test_prompts.py`): one, which cuts the paragraph out of `PLANNER` and checks D1–D3's words in it, that it sits before the JSON block, and that `PLANNER_GENERAL` asks for no mock-up. It fails without the change. The existing `test_the_planner_prompts_still_fill_in` covers the new `{card}` field.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The brief described the switch, the copied Today and the marks, then said "as `docs/milestones/f17-mockup/top-bar.html` does". That file has none of them: one dimmed "Today, on a phone (for comparison)" block drawn by hand. A planner following the example would draw the old layout | Fixed: F17 stays as the example of real values, and the brief adds "for the switch, the copied Today and the marks, follow `docs/milestones/f94-mockup/away-rows.html`". The test checks the brief names that file and that the file has the switch |

Read and found sound, no finding:
- The three texts agree: the brief, `lead.md` and `owner.md` give the same trigger and the same exceptions.
- The new paragraph doesn't contradict the one before it, which already asks for one self-contained file and lists what the frame refuses. A switch needs a script, which the frame runs (F104).
- The paths the brief gives exist: `factory_dashboard/static/dashboard.css`, both template folders, both example files.
- Neither example sits Today and Proposed side by side on a wide screen, as D2 asks. The brief's words ask for it; see "What next".

Edited existing tests: none (18 lines added to `tests/runner/test_prompts.py`, none removed). The review added four lines to the new test for F1.

No checkpoint ran on this ticket (a lead ticket), so there are no checkpoint findings to judge. French: nothing to check, no user-facing string and no `coucou/locale/` file changed. Screenshots: no new screen. After the fix, `uv run pytest -q tests/unit tests/integration tests/runner` gave 1819 passed, 1 skipped; ruff is clean on the two edited files.

Score: 9/10. Small, faithful to the plan's four decisions, with a test that reads the right paragraph. It lost a point for an example that didn't show what the sentence before it asked for.

Stop reason: none; nothing is left for a round 2.

## Factory
- **The flow:** one lead ticket, one attempt, no stop, no park, no intervention from you. The runner restarted after the merge, as it must when `runner/` changes.
- **Models:** Claude Opus only; see the numbers below. No developer work, so "Known range" in `docs/agents/lead.md` has nothing new.
- **What to change:**
  - A lead ticket still gets no checkpoint, so its review is its only reader (F41, F53, F55 and F79 said the same). Here the one finding was small.
  - A rule written into a brief is only as good as the next job's reading of it. Nothing checks that a frontend plan carries a mock-up. I'd not add a gate yet (low ceremony): if a frontend card arrives without one and without a reason, the fix is a pre-flight line in `runner check-tickets` that asks for a mock-up path in a ticket touching a template.

## Workflow observations
- The start tag was right and the diff held only F72's work: nothing was committed between the merge and this review.
- The review also wrote the narrative of the build session and F72's entry in ADR 02's learnings log.

<!-- runner report -->
<!-- /runner report -->
