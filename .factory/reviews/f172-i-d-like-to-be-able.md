# Review: F172, a card marked to use Claude's reserve

## Sign-off sheet

### 1. What changed
You can now let one card use Claude's reserve without turning on the reserve for everything. A card's page has a lever under its title, "may use Claude's reserve". Pull it, and that card's lead tickets (plus any ready tickets they wait for, even on other cards) keep running past the week's 70% mark and past your 25% of the 5-hour window, while both switches stay off. Every other lead ticket still waits as before. The mark ends by itself when you sign the card off. The board shows a striped "uses Claude's reserve" plate on a marked card, and the Overview names the marked cards once, under Claude's meters ("Past both marks for: …"). A real limit (a window at 100%) still stops a marked card's tickets.

### 2. How to test it yourself
1. With both reserve switches off, open a planted or growing card that still has ready lead tickets (on the board, then its page).
2. Pull "may use Claude's reserve". It turns dashed orange at once and can't be pulled again until the runner takes it at its next pick.
3. After that pick, reload: the lever is on, the board's card has the "uses Claude's reserve" plate, and the Overview's allowance panel says "Past both marks for:" with that card's link.
4. Next time Claude's week is past 70%: that card's lead tickets still run after the developer tickets, and other cards' lead tickets show under Needs you, waiting for the week's switch.
5. Pull the lever off: the plate and the Overview's line go after the next pick.
6. Sign off a marked card: its page no longer shows the lever, and the board no plate.

### 3. Left for later
- `/live` (refreshed every 5 seconds) now builds the board twice; harmless today, in `docs/backlog.md` to share one build.

### 4. Decisions waiting for you
None. [ADR 34](../adr/34-a-card-may-use-the-reserve.md) was accepted before the work started.

### 5. How the work went
- 2026-10-22 23:31 ([session](../sessions/2026-10-22-2331.md)): `f172-01` (the runner honours the mark) built by the lead, first time, 9 minutes; 0 local tokens.
- 2026-10-22 23:45 ([session](../sessions/2026-10-22-2345.md)): `f172-02` (the lever's request writes the mark) built by the lead, first time, 8 minutes; 0 local tokens.
- 2026-10-22 23:57 ([session](../sessions/2026-10-22-2357.md)): `f172-03` (the lever, the plate, the Overview's line) given to the local developer: three 20-minute attempts with no edit at all (2.1M local tokens), the third after a direction; then the lead did it in 20 minutes.
- Lessons:
  - The local developer never started f172-03: seven files over three pages and three large test files is past it, even with a direction. It should never have gone to it. By F14's rule a ticket adding to `test_planning.py` is the lead's. The escalation added that to `docs/agents/lead.md` ("Known range", F172): check every dashboard ticket against F14 at planning.
  - The runner tickets were clean and well tested, including the hard cases: a dependency on another card passes too, and a real limit still holds.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** the planner keeps routing dashboard tickets that span several pages to the local developer. A check would catch it: `softfield check-tickets` could refuse `agent: developer` on a ticket whose `tests:` names `test_planning.py` or more than one page's test file. That turns the F14 rule from a line in `lead.md` into a gate. I'd plant it as a card. Text ready to paste in the Plant box: "check-tickets refuses a developer ticket the local model can't do: one that adds to test_planning.py or spans more than one page's module (F14's rule, broken again by f172-03)."

### 7. What clogged the factory line
- **60 minutes of local attempts that made no edit** (f172-03, 00:00 to 01:00): with the ticket routed to the lead at planning, these would have gone. Fix: the check above.
- **Two runner restarts** (about 3 to 5 minutes each, after f172-01 and f172-02): the designed stop when `runner/` changes. Nothing to unclog.
- No limit waits and no stops for you.

## What was built
- `runner/milestone.py`: `Card.reserve` read from the header's `**Reserve:** yes` (D1).
- `runner/loop.py`: `reserve_cards` (a marked card's ready tickets and, transitively, the ready tickets they wait for, across cards; D3). `at_reserve`, `at_five_hour` and `_waits_for_the_owner` let them pass; `_next_task` takes developer tickets first, then the marked ones, before parking a lead ticket.
- `runner/requests.py`: a `reserve` request whose subject is a card's short key writes or removes the mark in a commit of its own (after Area, else Priority, else State), waits for a clean main like other committing requests, and frees the card's tickets parked at either reserve, resolving their Needs-you items (D2, D4). `take_switches` leaves it for the pick.
- `runner/owner.py`: sign-off drops the mark (D5).
- Dashboard: the lever on the card's page (`thread.html`, `_reserve_lever`), the board's plate (`board.html`, `Card.reserve`), the Overview's line under Claude's meters (`_partials/allowance.html`, `reserve_marked`), CSS in the theme's hazard stripe (D6), all as the mock-up.

Tests: 5 loop tests (week mark, 5-hour mark, dependencies across cards, ready tickets only, a real limit still holds), 7 request tests, a milestone and a sign-off test, and 11 dashboard tests including a Chromium click. One existing test changed: the refusal text for `reserve month on` in `test_requests.py`, which follows the new request's wider subject. It is an honest change.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | nit | claude | The lever showed on a growing card with every ticket done (waiting for its review), against D6 | Fixed: no lever once every ticket is done; F25 added to `test_an_idea_ripe_or_done_card_has_no_lever` |
| F2 | nit | claude | Sign-off's mark removal ate the space before a field after it | Fixed: lazy match up to the next ` · `; a second case in `test_a_card_signed_off_drops_its_reserve_mark` |
| F3 | nit | backlog | `/live` builds the board twice per 5-second poll | In `docs/backlog.md` |

No checkpoint ran (two lead tickets and one escalation the lead finished), so there are no checkpoint verdicts. Score: 8/10. The runner side is careful and well tested, and every decision is followed. The two slips were small edge cases on the edges of D5 and D6. The routing of f172-03 cost an hour of the line.

Checked and fine: the lever's `hx-vals` escape the project and key (`tojson`); the runner refuses a subject that isn't a short key (`../f142` is tested), a card that isn't ready or building, and a missing doc; the mark is only read from the header, not the body. The planner's state rewrites (`planner.py`) touch only the State value, so they keep the mark. Ruff and mypy pass. All 794 tests in the files this milestone touched pass, and so does the rest of the runner and dashboard suite as far as it ran. The full run was stopped at its 10-minute limit at about 78%, with no failure up to that point.

The French: no `coucou/locale/fr/` change in this milestone.

## Factory
- Flow: two lead tickets merged first time; one developer ticket escalated after three no-edit attempts and a direction, then built by the lead. No stops for the owner, no limit waits, no parks. Two designed restarts for `runner/` changes.
- Models: Claude Opus about $7.24 in all (f172-01 $2.16, f172-02 $1.54, direction $0.61, escalation $2.93). Local Qwen 2.1M tokens, nothing merged.
- What to change: routing at planning. F14's rule exists and was broken again (F30, F17, now F172). Since it recurs, it should become a check (see "What next"), not one more line in `lead.md`.

<!-- runner report -->
<!-- /runner report -->
