# Review: F103 the Planning tab counts only what you have to answer

- **Status:** review round 1 done, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- The number next to **Planning** no longer counts seeds (ideas you planted but haven't sent to the lead). It counts only what you have to act on: answers wanted, proposals to review, notes that didn't go through, blocked tickets and cards to sign off.
- "Your desk · N" on `/planning`, the Overview's "N things wait for you on your desk" and the Projects page's "N for you" follow the same number.
- Seeds are still listed on the desk, last, under "Seeds, not asked about yet · N", with their own number.
- Previous / Next between desk pages no longer steps through seeds. On a seed's page, Next leads to the first thing that waits for you.
- On today's data the tab reads "Planning · 25" (1 blocked, 6 to sign off, 9 answers, 9 proposals), and the 2 seeds are left out.

### 2. How to test it yourself
1. On the phone, open the dashboard: the tab reads "Planning · N".
2. Open `/planning`: N equals "Your desk · N" and the sum of every group's number except Seeds.
3. Plant an idea with **Plant** only (not "Plant and ask the lead"). Once the runner has picked it, it shows under Seeds, whose number goes up by one. The tab and "Your desk" keep the same number.
4. Open that seed's page: Next takes you to the first card that waits for you, not to another seed.

### 3. Left for later
Nothing from this card.

### 4. Decisions waiting for you
None.

### 5. How the work went
- [2026-10-29 09:14](../sessions/2026-10-29-0914.md), [10:51](../sessions/2026-10-29-1051.md), [11:05](../sessions/2026-10-29-1105.md) and [14:35](../sessions/2026-10-29-1435.md): `f103-01-seeds-not-counted` was escalated. Qwen made no edit in three 20-minute attempts (2, 2 and 10 steps), the third under a direction ($0.51). The direction waited 5 hours for Claude's window. The lead finished it in the escalation in 8 minutes ($1.17).
- Lessons:
  - A one-line filter at difficulty 2 stopped like the difficulty-4 tickets the same night (f73-01, f73-02). The model was slow that night; the ticket's size wasn't the cause. bug-48 (ready) skips the direction and escalates at once when that happens.

### 6. What next
- **Product:** on hold, as you asked (2026-10-04).
- **Factory:** run bug-48 before the next batch of developer tickets. It would have saved this card $0.51, 20 minutes of Qwen and a 5-hour wait.

### 7. What clogged the factory line
- **5 hours waiting on the direction** (10:42 → 15:43 on 2026-10-29): Claude's window was full, and the ticket was parked across three runs. Fix: bug-48. With no direction, the ticket goes straight to escalation, one Opus job instead of two.
- **1 hour of Qwen with nothing merged:** three no-edit stops. Fix: the same bug-48.
- No stops for you, and no ticket waited on another.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/planning.py`: `waiting_for_you` leaves out the group whose key is `seeds` (D1). Every count reads it: the tab (`app.py`), the desk heading, the Overview (`overview.py`), the Projects page (`projects.py`) and `desk_trail`. `desk` still returns the Seeds group.
- Tests: two new in `test_overview.py` (seeds plus one answer wanted count as 1, and with seeds only Needs you has no desk line and the tab has no number, while the desk still lists them). Four existing tests were edited:
  - `test_app.py` `test_every_page_shows_the_planning_count_on_first_paint`: was a loose `\d+` match fed by two seeds. It now pins 1, then 1 after two seeds, then 2 after an answer wanted. Stronger than before.
  - `test_planning.py` `test_group_headings_count_what_waits_and_add_up_to_the_desk`: the sum leaves Seeds out and pins its heading at 1. `len(headings) > 2` is a fair tightening.
  - `test_planning.py` `test_a_group_heading_leaves_out_what_is_on_its_way` and `test_desk_heading_leaves_out_what_is_on_its_way`: the sums leave Seeds out. The latter first asserts the seeds group has links, so leaving it out is not an empty no-op.
  - `test_planning.py` `test_previous_and_next_step_through_what_waits`: rewritten for the new trail, which now pins "3 of 3", no Next from the last item, and a seed page's Next. Exact where it used to be loose.

## Findings and resolutions

| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f103-the-number-of-things-in-planning-F1 | nit | claude | The escalation's Known range line in `docs/agents/lead.md` asked for a runner check that already exists as bug-48 (ready) without naming it. | Pointed the line at bug-48. Resolved. |

Checked and fine:
- On real data (`softfield look page /planning`): tab and desk both read 25 = 1 + 6 + 9 + 9, with Seeds · 2 listed and not counted.
- Every Done when has a test, except the Projects page's "N for you". That count reads the same `waiting_for_you`, so it follows by construction, and it isn't worth a test of its own.
- The affected tests pass (35 selected across the three files).
- No French: the dashboard is English only. No screenshot: nothing on screen moved (D3).

No checkpoint read this ticket, so there are no checkpoint findings to judge, and none is marked missed.

**Score: 8 of 10.** The change is right and minimal, as D1 asked, and the edited tests are stricter than before. The score is held back by the cost of getting it there: three no-edit attempts and a direction for a one-line filter.

## Backlog
None.

## Workflow observations (Factory)
- **Flow:** one developer ticket, 0 of 3 attempts with an edit, one direction that waited 5 hours for Claude's window, one escalation. No stop, no park beyond the wait for the window, no intervention by the owner.
- **Each model:** Qwen (qwen3.6-35b-a3b), 1 hour of model and no edit. Opus $2.46: planner $0.78, direction $0.51 (changed nothing), escalation $1.17 (did the work).
- **What to change:** bug-48 is already ready. This card adds evidence that the cause is the night, not the ticket: the smallest ticket of that run stopped the same way as the biggest.
