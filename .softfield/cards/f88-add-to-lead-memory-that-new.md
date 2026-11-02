# Milestone F88: add to lead memory that new software factory features…

> **State:** done · **Priority:** 1 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-20. Base: git tag `f88-add-to-lead-memory-that-new-start`. Report: [`.softfield/reviews/f88-add-to-lead-memory-that-new.md`](../reviews/f88-add-to-lead-memory-that-new.md).
> Planted by the owner on 2026-10-09.

## Notes
add to lead memory that new software factory features should be done with the main theme. the inspiration source is arknight endfield factory system, the colors are inspired from that. it should be subtle though and not copyright issue so be careful. but all new features should be designed with that in mind rather than bland. i can tone down if necessary in proposals/mock ups, rather than tone up to be more fun

## Expected outcome
Every new factory page, element and mock-up is drawn in the factory theme from its first draft, a little bolder than needed, so the owner tones it down rather than asking for more. The theme is described in plain traits any agent can follow, and nothing in it is taken from the game.

## Done when
- `docs/agents/owner.md` carries the rule (D1–D4), dated 2026-10-09, in a few lines.
- `docs/agents/lead.md` (Planning room) points at it in one line.
- `PLANNER`'s mock-up paragraph (`runner/prompts.py`, added by f72-01) says a mock-up's Proposed is drawn in the factory theme, leaning bolder; a test checks it.
- The next factory card with a mock-up is themed without being asked.

## Decisions
- **D1 The theme is the dashboard's own look, named in traits.** The source is `factory_dashboard/static/dashboard.css`'s tokens and fonts, not the game: a dark industrial floor with bays and plates (a pale one in the light theme), hazard yellow and stripes, angular display type (Chakra Petch), technical labels in mono, thin rules and a faint grid, corner ticks and panel headers like equipment plates, machines, belts and crates. New features reuse these tokens; a new colour or shape joins the tokens first.
- **D2 Inspired, never copied** (the owner: "subtle, not a copyright issue"). Arknights: Endfield is named only in `owner.md` as where the mood comes from. No names, logos, characters, icons, screenshots, sounds, game fonts or traced layouts from it; the word never appears on a page or in an asset. Every drawing is our own SVG or CSS; fonts stay open-licence (Chakra Petch, Barlow and JetBrains Mono are OFL).
- **D3 Decoration never looks like a status.** The owner's "no unexplained marks" (2026-10-02) still holds for anything that could be read as information: colours that mean something (the agents' colours, fail, warn, good) keep their meaning and aren't used as ornament. Ornament (ticks, stripes, grid, plate headers) uses the ink, rules and the hazard stripe only, and never blinks or counts.
- **D4 Lean bolder in proposals.** A mock-up's Proposed shows the themed version first; where a choice is a matter of taste, it may show a calmer variant beside it. The owner tones down.
- **D5 The factory only.** Mum's product (`coucou/`) keeps its calm, ambient look (owner.md, "Product taste").

## Tickets
| # | id | who | diff | depends | what |
|---|----|-----|------|---------|------|
| 01 | f88-01-factory-theme-rule | lead | 2 | f72-01 | D1–D5 in `owner.md`, a line in `lead.md`, a sentence in `PLANNER`'s mock-up paragraph, with a test |

## Later
- F81 (the owner's assessment of today's pages, same day) applies the theme to what already exists; F88 only sets the rule for new work.
