# ADR 35: No backlog file: fixes are bug seeds, ideas are planted

- **Status:** Accepted (by the owner, 2026-10-28)
- **Date:** 2026-10-27
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** `docs/workflow.md`, "Milestone review loop" (where nits and should-fix points about untouched code go) and "Discoveries" (where the inbox is triaged to).
- **Evidence:** F149 (owner, 2026-10-16: "is docs/backlog.md still used? i thought that one was retired"; 2026-10-27: "factory reviews still seem to write to it … delete it for all projects and ensure it stops getting written"). The file is shown nowhere on the dashboard, yet the `REVIEW` prompt (`runner/prompts.py`) and the re-review scope (`runner/milestone.py`) still send findings to it: Softfield's holds 30 items, Travel companion's 17 from five reviews (2026-10-20 to 22), Coucou's 18. The f5-13 pass (2026-10-23) already turned 43 of Softfield's into set-aside bug tickets, which the board shows as seeds.

## Decisions
1. **A finding worth a fix becomes a bug seed.** A nit, or a should-fix point about untouched code, that is worth a run is written by the review as a bug ticket set aside in `.softfield/tasks/later/` (`milestone: bugs`, its `area:`, `finding: <id>`): the board shows it as a seed and the owner queues it by dragging. Its route is `later`; it replaces `backlog`.
2. **A finding not worth a run is said once, in the review report.** Its route is `report`: it stays in the review's findings (the report and the metrics database), and nowhere else. "If it ever happens" notes go here.
3. **An idea that needs a card is a quoted line** in the sign-off sheet's "What next", which the owner plants from the dashboard (F164 D1). A review never writes a note to a file for later.
4. **Checkpoints' findings without a fix ticket take the route `report`**; the review judges them as today (ADR 14 item 13).
5. **`docs/backlog.md` is removed in every project**, its items each made a bug seed, a planted card, or dropped with a reason. Old review files that say `backlog` still read.
6. **Discoveries stay** (`.softfield/discoveries.md`, the developers' inbox): the review triages it into bug seeds, tickets or ADRs.

## Alternatives turned down
- **A planted card per item:** about 65 items in three projects, mostly one-line nits, would bury the 36 ideas on the board. A bug seed is the board's card for a fix already.
- **Keep the file and show it on the dashboard:** a second list beside the board, which the owner wants to be the only order (2026-10-22).

## Consequences
- The review writes more set-aside bug tickets; a review that writes many seeds of one area should group them into one ticket per file.
- `ROUTES` (`runner/review.py`) becomes `local`, `claude`, `adr`, `later`, `report`, with `backlog` still accepted from old files.
