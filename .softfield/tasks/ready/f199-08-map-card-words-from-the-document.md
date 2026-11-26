---
id: f199-08-map-card-words-from-the-document
milestone: f199-let-s-improve-the-factory-floor
agent: lead
difficulty: 4
depends_on: []
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
finding: f199-06-fix-map-taps-checkpoint-1
---

### Goal
Every map tap opens a card whose words and numbers come from the live document: a seed, a belt, sprouting, a queue crate and a machine included.

### Context
`showMapCard` in `factory_dashboard/static/factory.js`, after f199-06; the original asks are in `.softfield/tasks/done/f199-04-map-taps.md`. A developer already failed this fix once (f199-06), so it's the lead's.
- A tap on Seed (`data-what="seeds"`) opens nothing: f199-06 removed the `key in WHAT` branch and no branch handles `seeds`, so it falls through to the machine lookup and returns. f199-04 asked for the set-aside list `showSeeds` gives, plus a link to `/board`.
- A belt's card reads `BELT_LABELS`, whose 13 entries all say "Cards move this way when you plan and approve them.", and it shows no count. Each belt in `doc.belts` carries its own `label` and `today`: f199-04 asked for "your sign-off" and "7 went this way today".
- Sprouting's card counts `doc.field.planted`, the planted cards, not the sprouting count in `doc.stations`.
- A queue crate's link goes to `/tickets` for every crate, not to the crate's own ticket (`/tickets/<id>`, as `showSeeds` links them).
- The machine card's `/agents#<station>` link has no project query; the sprouting and machine words still carry the mock-up's "On the page: …" notes.
- `WHAT` and `BELT_LABELS` are no longer needed for anything correct; `WHAT` still holds one day's hard-coded counts.
- Tests that hide these: the station-tap test leaves Seed out; the belt test accepts "Cards move"; the machine test passes on `"on" in card_text`; the 44 px test passes a target when either side is 44 (a 200×4 belt passes).

### Done when
- a tap or Enter on Seed opens the set-aside list with a link to `/board`
- a belt's card shows that belt's own `label` and "N went this way today" from `today`; two different belts show different words
- Sprouting's card shows the sprouting count from the document
- each queue crate on the card links to its own ticket page, with its project's query
- the machine card's link keeps the project query, and no card shows "On the page:"
- the weakened tests above check what a person sees: the words and numbers, not that something is there
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
