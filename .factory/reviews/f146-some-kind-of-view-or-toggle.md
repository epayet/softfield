# Review: F146 the board's developer's view

- **Status:** review round 1 done, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- The board has a **developer's view** lever, after the kinds (All, Factory, Product, Bugs). Turning it on opens the same board, with every card in the same place, but each card now says what it holds for the developers:
  - **lit** (blue edge): "developers: 1 now · then Claude's review" or "developers: 3 now · then the lead's f81-07-…": developers can take these tickets without the lead;
  - **half-dark**: "2 developer tickets wait for f132-02-…": their work waits for the lead ticket that is named;
  - **faded**: "lead only", or "every ticket done · then Claude's review" on a card whose tickets are all merged. The other stages fade whole ("no ticket to run"). A faded card comes back when you hover over it or tap it.
- The Planted stage's head adds up the lit cards. On today's queue it says: "Developers can work on 9 cards, 11 tickets, about 13 h 59 min, before every developer ticket left waits for the lead".
- Search and the kinds keep the view on. Drag, ⋯ and Send new order work exactly as in the normal view and send the same request.

### 2. How to test it yourself
1. On the phone, open **Board** and tap **developer's view**. The lamp lights, and a legend at the bottom of the field explains lit, half-dark and faded.
2. In Planted, find F81: it should read "developers: 3 now · then the lead's f81-07-no-inline-styles". Then find F132: "5 developer tickets wait for f132-02-overview-live-every-project".
3. Type a word in Search, or tap Factory: the lever stays on.
4. Drag a lit card above another one and press **Send new order**. The card shows "on its way", just like in the normal view.
5. Tap the lever again: you are back on the normal board, with no developer words on it.

### 3. Left for later
Nothing from this card.

### 4. Decisions waiting for you
None.

### 5. How the work went
- [2026-10-29 11:05](../sessions/2026-10-29-1105.md): `f146-01-developer-line` (a lead ticket, on Sonnet) was parked by Claude's limit after a first try.
- [2026-10-29 14:35](../sessions/2026-10-29-1435.md): `f146-01` merged at its second try (11 minutes). `f146-02-developers-only-view` was escalated: in attempts 1 and 2 Qwen made no edit. Attempt 3, under a direction, made six edits but left `card_link(c, view)` calling a one-argument macro, which broke every board page (47 tests failed). It wrote no CSS and no tests. Opus finished the work on the branch in 13 minutes.
- Lessons:
  - This is the same night pattern as F103 and F172: Qwen was slow and made almost no tool calls. bug-48 (ready) is the fix.
  - Passing a new argument to a macro whose `{% macro %}` line doesn't take it breaks every page that uses it. The escalation added this to `docs/agents/developer.md` as an example to follow.

### 6. What next
- **Product:** on hold, as you asked (2026-10-04).
- **Factory:** today's view shows that only 11 of the 97 ready tickets can run without the lead, and the half-dark cards point at a few lead tickets that hold the most developer work: f132-02 (F132, F62, F97, F124) and f9-29 (F61, F77). Dragging those cards up is the cheapest way to keep Qwen busy overnight. Running bug-48 first would have saved this card's two hours of Qwen and its direction.

### 7. What clogged the factory line
- **About 6 hours waiting for Claude's window** (11:46 → 17:38 on 2026-10-29): `f146-01`, a lead ticket, was parked by the limit. Fix: none needed for this card. The fast lane (F191, sprouting) and Claude's reserve mark (F172, ripe) are how to put a card like this ahead.
- **About 2 h 15 of Qwen with nothing merged** (17:54 → 20:12): two no-edit stops, then a third attempt that broke the page. Then a 36-minute wait before the escalation. Fix: bug-48 (ready), which escalates at once on a night with no-edit stops.
- No stops for you. `f146-02` waited on `f146-01`, as planned.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/board.py` (`f146-01`, by the lead):
  - `DevWork` on each `Card`.
  - `_developer_ticket`: the runner's own `lead_only` rule, with protected paths read from the checkout (D1).
  - `_dev_resolver`: the lead tickets a developer ticket waits for, followed through other developer tickets, with a cycle guard (D2).
  - `_dev_work`: a card's look (D3).
  - `Board.developers`: the totals, with the tickets times the median of `ticket_minutes` (D4).
  - With `developers=False` nothing changes, and a test pins that `line` is the same either way.
- `board_page`, `board.html` and `dashboard.css` (`f146-02`, finished by the lead):
  - `view=developers`, the lever as a link that keeps the project, the search and the kind.
  - A hidden `view` input in the filter form.
  - The `dev_tag` macro.
  - The `dev-view` field and its legend, using the existing lever's look and the `--dev` and `--opus` tokens.
  - `_hours`, which writes times as "5 h 05 min".
- Tests: 9 for the data and 5 for the page, one of them a browser drag and send from the view. No existing test was edited.

## Findings and resolutions

| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f146-some-kind-of-view-or-toggle-F1 | should-fix | claude | A planted card whose tickets were all done (F146 and F185 while their reviews ran) said "lead only", when what was left is Claude's review. | `_dev_work` gives such a card `then="review"`, and it reads "every ticket done · then Claude's review". A new test covers it. Resolved. |
| f146-some-kind-of-view-or-toggle-F2 | nit | claude | The board-totals test asserted `minutes is None or minutes > 0`, which can't catch a wrong time. | It now asserts `(1, 2, 20.0)` exactly. Resolved. |

Checked and fine:
- On real data (`softfield look page "/board?view=developers"`), every card's words agree with the others. Two examples: F37 waits for f67-02, and F67 reads "lead only". F132's five tickets wait for f132-02. The totals equal the sum of the lit cards (9 cards, 11 tickets).
- The lever's own `.slot` sits outside `#field`, so `board.js`'s `.slot` queries and the `.dev-view .slot` rules never reach it.
- Faded cards use opacity .32, as in the mock-up. They come back on hover or focus, and a dragged card keeps full opacity.
- No French: the dashboard is English only. No screenshot, because this job has no browser. The browser test covers the drag and send.

No checkpoint ran on this card, so there are no checkpoint findings to judge and none to mark missed.

**Score: 8 of 10.** The data follows the card's decisions closely and reuses the runner's own rule, and the tests are thorough. The score is held back by the developer ticket: two hours of Qwen and a broken page before Opus finished it, plus one misleading wording.

## Backlog
None.

## Workflow observations (Factory)
- **Flow:**
  - One lead ticket, parked about 6 hours by Claude's limit.
  - One developer ticket: 3 attempts, one direction, then an escalation.
  - No stop, and no intervention by the owner.
- **Each model:**
  - Sonnet did the lead ticket well at its second try.
  - Qwen (qwen3.6-35b-a3b) used 2 h 15 of model time and merged nothing. Its third attempt broke every board page.
  - Opus ran the two planners, the direction and the escalation.
  - The dollars are in the runner's report above.
- **What to change:** bug-48 is already ready, and this card adds evidence for it. The view this card built is also the tool for the owner to steer the queue: dragging the lead tickets that hold the most developer work to the top keeps the local model fed.
