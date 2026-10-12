# Milestone F90: editing seeds that i've planted but not sent to the lead…

> **State:** ready · **Priority:** 2 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
editing seeds that i've planted but not sent to the lead don't show the whole text. example: is the planning conversation efficient atm, in terms of…

## Why it happens
A plain Plant (no "ask the lead") writes the card with the note's first words, cut under 60 characters, as its title (`heading` in `runner/planner.py`, F31 D7), and the whole note under `## Notes` in its doc. The seed's page (`thread_page` in `factory_dashboard/planning.py`) shows only that title (`_header`, from the `milestones` row) and an empty reply box: the whole note is never on the page. F83's card is the example: its title ends "in terms of…", and "claude token usage?" is only in `docs/milestones/f83-is-the-planning-conversation-efficient-atm.md`.

## Outcome
A card's page shows the owner's whole note, so they can read what they planted before sending it to the lead, and after.

## Done when
- F83's page shows "is the planning conversation efficient atm, in terms of claude token usage?" whole, under its title
- an idea card with no thread shows its note above the reply box; a card with a thread shows it folded ("Your note"), so a long thread isn't pushed down
- a card whose doc has no `## Notes` (or "(none)") shows nothing extra

## Decisions
- **D1. Show the note, don't edit it.** What the owner adds goes in the reply box: the lead reads the card and the message together, so a correction there reaches it just the same. Editing a card's doc from the dashboard would be a new request kind writing to main (a protected `factory_dashboard/requests.py` change and a runner handler), for no gain the reply box doesn't give.
- **D2. Read from the doc, not the database.** The `milestones` row has no notes; the page reads `## Notes` from the card's doc in the project's checkout (`_repo`), as `_adr_waits` reads ADRs. No checkout (a URL): nothing shows.

## Tickets
- `f90-01-seed-shows-its-note`
