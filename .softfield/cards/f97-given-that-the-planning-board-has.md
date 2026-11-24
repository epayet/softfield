# Milestone F97: Needs you steps aside: Now first, a box of desk counts at the bottom

> **State:** ready · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-10-10.

## Notes
Given that the planning board has notification number that shows clearly that I have actions to do. The overview needs you part seems irrelevant now. Or perhaps not so prominent at the top, a box at the bottom could be enough

## What happens today (from the code and the dashboard, 2026-10-27)
- Needs you is the Overview's first panel, above Now (`factory_dashboard/templates/overview.html`, the `#live-needs-you` poller). On softfield today it holds one line: "25 things wait for you on your desk", the desk's top three titles and "Open your desk ›". The Planning tab says the same 25 (`planning_count`, both from `waiting_for_you`).
- What Needs you holds besides the desk is on no desk: a runner stopped mid-job, tickets waiting while the runner is idle, a check failing on main, Claude's allowance questions, an ADR, a review that stopped (`needs_you` and `_live_context` in `factory_dashboard/overview.py`). Open now: two allowance questions on travel-companion.
- The Planning tab counts only the picked project's desk; the Projects page lists every project's ("travel-companion · 1 item on the Planning desk").
- F132, One view of the whole factory, is about to rework the same panel (its D6, ticket f132-02): one desk line per project, with its top three.

## Expected outcome
Now is the first thing the Overview shows, on a phone too. What waits on the owner sits in a box at the bottom: one plate per project's desk with its count, then whatever is on no desk. Only what stops the line (the runner stopped, main red, an idle queue) shows near the top, inside Now, where it explains what Now shows.

## Done when
- f97-01 to f97-03 merged.
- On a phone the Overview doesn't scroll sideways, and travel-companion's two reserve questions are gone from Needs you.
- To test: open the Overview on a phone. Now is the first panel. Scroll to the bottom: Needs you shows "25 · softfield desk ›" (and travel-companion's and coucou's), each opening that project's Planning room, then travel-companion's two allowance questions. The Planning tab still says 25, and phone notifications come as before.

## Decisions
- **D1. Now comes first.** Needs you leaves the top of the Overview for the bottom, after While you were away (the last panel once f132-04 moves Savings away). The page keeps its one poller, moved with it.
- **D2. A desk is a count.** Each project's desk line becomes one plate: its count, its project, "desk ›" to its Planning room; no titles (the desk lists them, the tab counts them). This replaces F132's D6 desk line (top three, "Open ›") once f132-02 has built it.
- **D3. What stops the line stays near the top, inside Now**: a runner stopped mid-job, tickets waiting while the runner is idle, a check failing on main, as a "Line stopped" strip at Now's top. They are why Now looks wrong, and a box at the bottom of a phone page would hide them.
- **D4. The rest stays in the box**, under the desks, as drawn today: an ADR, Claude's allowance, a review that stopped, any other kind. The box shows only when something is in it.
- **D5. Unchanged:** the Planning tab's count, the phone notifications (`data-notices`), the desk itself.

### After the build (owner, 2026-11-24: "There is horizontal scrolling issue on mobile on overview page now, is this from here? The reserve questions I can't do anything about them why are they still there")
- **D6. The sideways scroll comes from F210's strip, not this card** (f97-02). F210, One strip of steps, styled its card-steps strip with bare `.steps` rules on 2026-11-10 (`ed213827`). Those rules also hit the Overview's `ul.steps` lists (While you were away, Needs you). Their rows lost their grid, and every link became a 44 px uppercase plate that doesn't wrap, so a ticket's name runs past a 390 px screen. f97-01 added no rule that can overflow (its plates and strip all wrap). The fix scopes F210's rules to `#card-steps` and adds a whole-page phone check of the Overview, which had none with long names.
- **D7. A lapsed lever asks nothing** (f97-03; replaces ADR 22's "the runner asks again", owner, 2026-11-24). Since ADR 50 item 6, a "keep the board's order" lever that is off only lets lead tickets go after the developers' past the mark. Nothing waits for the owner. Yet each lapse opened a Needs-you item and a notification, and only a request from that same project answered it: travel-companion's two, from 2026-10-23, still sit in the box with their old "use the reserve" words. The lever now turns off quietly, and a run's start answers every open `reserve` item.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | needs-you-steps-aside | D | 3 | f132-02, f132-04 | D1–D5 |
| 02 | card-steps-styles-stay-in-the-strip | D | 2 | – | D6 |
| 03 | a-lapsed-lever-asks-nothing | L | 3 | – | D7 (`runner/` is protected) |

It follows f132-02, which reworks the same panel and `_live_context`, and f132-04, which changes the same template; a developer's, since it moves panels and splits a list the code already builds.

The mock-up: `.softfield/cards/f97-mockup/overview.html` (Today and Proposed, real values of 2026-10-27).

## Before and after
- `/`
