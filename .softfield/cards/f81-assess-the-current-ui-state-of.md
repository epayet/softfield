# Milestone F81: Bring the factory theme to the older pages, the Planning room first

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
assess the current UI state of the factory and share opportunities to be funkier and cool inspired by Arknight endfield (in a sublte way, not an obvious copyright issues type of way). i'm open to ideas

The owner, 2026-10-26: "Some of it was designed with arknight in mind some not. Let's assess current state and improve"

## Expected outcome
Every factory page wears the theme F88 set for new work, not only the parts built since: each panel is a plate with a striped header and corner ticks, tags and buttons are angular, numbers read as readouts, and the Planning room, its threads and proposals look like the rest of the floor. Nothing that means something changes colour or meaning.

The picture: [`f81-mockup/theme-pass.html`](f81-mockup/theme-pass.html) (Today against Proposed, with a calmer variant).

## Done when
- Overview, Tickets, Jobs, Runs, Timeline, Agents, Bench, Planning, a thread and a proposal show plate headers and corner ticks on every panel, in both themes.
- No rounded corner is left in `dashboard.css`; an empty panel shows the idle crate.
- `planning.html`, `thread.html` and `proposal.html` carry no `style=` but the computed widths and positions of meters; a test holds it.
- The owner checks the Overview and the Planning room on the phone, both themes.

## Assessment (2026-10-26, from `dashboard.css` and the templates)
- **Themed already:** the top bar (hazard stripe, tab plate), the floor (machines, belts, crates, smoke), the board (plots, stage heads, area edges), the reserve lever, the set-aside plate (F159), the card page's "What it's about" (F158), the Projects page.
- **Plain:** the generic `.panel` every other page uses (a flat bay and a title, no plate or ticks); round pills, the crate card, `.empty` and the new-version note (rounded corners); stat boxes; the Queue panel's `h3` title, unlike the rest.
- **Out of the stylesheet's reach:** `planning.html` (80 inline styles), `thread.html` (81) and `proposal.html` (52): the owner's most used pages can't be themed from `dashboard.css` until their styles are classes. Each new desk ticket adds more.

## Decisions
- **D1 One plate for every panel.** `.panel > h2` becomes the plate header `.about` already draws (plate background, rule under it, the stripe filling the gap, `.src` in mono at the right), and `.panel` gets the corner ticks top-left and bottom-right. `.panel.needs` is the one yellow plate. No template changes for it: every page with `.panel` gets it at once.
- **D2 New tokens first.** `--tick` (ink-2), `--stripe` (the hazard stripe on transparent) and `--notch` (the cut corner's `clip-path`) join the top of `dashboard.css`, in both themes; `.about` and `.aside` move onto them.
- **D3 Ornament is ink and hazard only, never moves** (F88 D3): no ticks, stripes or grid in an agent's or a status colour, no new animation. The faint 32 px grid on the floor is `--grid`.
- **D4 No invented labels.** The game's look leans on serial codes and decorative captions; here every word on a page says something (owner, 2026-10-02), so plates carry the panel's own title and nothing else.
- **D5 One button set:** `.btn.go` (hazard plate, cut corner) and `.btn.plain` (outlined) in `dashboard.css`; the inline buttons in the three planning templates and the existing go-buttons (`.aside .go`, `.order-bar .go`, `.projects-page .send-order`) use them.
- **D6 The planning templates move to classes** (`.desk`, `.desk-item`, `.group-head`, `.tiles`, `.plant`, and the thread's and proposal's own), keeping every id, `hx-*` attribute and word; only a meter's computed `width`/`left` stays inline. `.softfield/developer.md` says so for new markup, and a test holds it (f81-07).
- **D7 After the desk work.** F81 sits after F132, F42, F73, F26, F63, F51, F74 and F75 on the board, which reshape the same pages: it themes their final markup. Moving F81 up means redoing those tickets' inline styles later.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | plate-panels | D | 3 | – | D1–D3: plate headers, ticks, tokens, the grid; Queue's title an `h2` |
| 02 | square-parts | D | 2 | 01 | square tags, no rounded corners, the idle crate, the meter's slot and gauge |
| 03 | one-button-set | D | 3 | 01 | D5 |
| 04 | desk-in-classes | D | 4 | 03 | D6 for `planning.html` |
| 05 | thread-in-classes | D | 4 | 03 | D6 for `thread.html` and `proposal.html` |
| 06 | now-readouts | D | 2 | 02 | Now's numbers as readouts, Next in line as a belt of rows |
| 07 | no-inline-styles | lead | 2 | 04, 05 | the `developer.md` note and the test that holds D6 |
