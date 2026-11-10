---
id: f9-29-week-pace
milestone: f9-line-polish
depends_on: [f9-28-allowance-live, f219-01-one-lead-rule]
agent: lead
difficulty: 3
files:
  - runner/allowance.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/runner/test_allowance.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview shows when Claude's week pacing holds lead tickets back: the week meter carries today's pace line and says in words whether the factory is on pace or over it, and a held lead ticket's row in Next in line says so, with until when.

### Context
Read `_check` in `runner/allowance.py` (a fixed window's pace line: `share * min(1, elapsed + MARGIN)`, ADR 25), `agent_allowances` and `WindowAllowance` in `factory_dashboard/overview.py` (the week's `mark` is the reserve, not the pace), the allowance partial f9-28 made, and the ticket rows of `factory_dashboard/templates/_partials/queue.html`.
- The picture to build: `.softfield/cards/f219-mockup/lead-stop.html` (Proposed; it replaces the f9 mock-up, and ADR 44 and `.softfield/cards/f219-lead-tickets-don-t-wait-on.md` D7 say why). The pace line is a dashed hazard post with a small flag; the stretch used beyond it is hazard-striped; under the meter, a plate with a short hazard-stripe edge (like `.reserve-bay`) reads "Over pace: lead tickets wait until about <day HH:MM>", and under it "developers, planning, reviews and the fast lane go on · today's pace N%". On pace, there is only the post and "on pace" on the meter's second line, no stripes and no plate. In the week's last hours the mock-up's other plate reads "Last hours: lead tickets may use the whole reserve, until <reset>", with "what's left at the reset is lost" (at 100%, that everything waits for the reset); no post. The mark's words are corrected as drawn: on the week, planning and reviews go on past the mark and lead tickets stop there until the last hours; on the 5-hour window, the rest is the owner's. The legend's line about the mark changes the same way, and two new legend lines say what the post and the stripes mean. New CSS uses the tokens only.
- The owner (2026-10-07): "i understand there is a pacing through the week logic for claude lead tickets, that's not quite visible on the dashboard whenever we hit that"; again on F116 (2026-10-27): "I want to be able to visualise when the claude pacing happens somehow". Today only the Tickets page's row reason says "over its pace line of N%".
- Whether a lead ticket is held comes from `lead_hold` in `runner/allowance.py` (ADR 44), and the "until about" time from `lead_goes_at` there, never a second check in the dashboard. Make the pace line a public, pure function in `runner/allowance.py`, used by `_check` too (today `_check` works it out inline), so the dashboard and the runner can't disagree. With the week's reserve lever on there is no pace line: draw neither post nor plate. The fast lane keeps its exception.
- A lead ticket's row in Next in line says what the mock-up draws, "waits for Claude's week pace until about <day HH:MM>", while `lead_hold` holds it, except for a card marked to use both reserves (`reserve_cards`, F172 D6), which isn't held. Developer rows never say it.

### Done when
- a unit test of the pace function at three points of a week, matching `_check`'s decisions, and one of the "until" time
- over pace, the week row shows the post, the striped stretch and the plate with "lead tickets wait until about …"; on pace, the post and "on pace", no plate
- in the week's last hours, the "Last hours" plate shows and there is no post
- over pace, a lead ticket's row in Next in line says "waits for Claude's week pace until about …", the same as `lead_hold`'s answer; a developer's row doesn't
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
