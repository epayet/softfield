# Milestone F300: Projects page: show the card you already asked for, not the plant button again

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-25.

## Notes
the factory project page shouldn't say plant and ask the lead for a stack if i've already planted and it's being worked on

## Expected outcome
Once the owner has pressed "Plant and ask the lead for a stack" (or "… to fix it") on `/projects`, the plate stops offering it. Until the runner's next pick it says the request is on its way, even after a reload; after that it shows the card the plant became (its key, title and where it is) as a link to its thread. The button comes back only when that card is done or removed and the app still has no stack (or is still broken). A crash the owner has already asked about leaves Needs you.

Tonight: coaster-ranker's stack was planted on 2026-11-24 (request 1725, "planted .softfield/cards/m13-give-coaster-ranker-a-docker-compose.md"), M13 is ready, and its plate still says "Plant and ask the lead for a stack".

## Done when
- coaster-ranker's plate shows "You asked the lead · M13 · Run coaster-ranker from the Projects page in Docker, retiring bin/live · ready", linking to its thread, and no plant button
- coucou's plate, never asked, still shows the button; after a press and a reload it shows the on-its-way line, not the button
- a crashed app whose fix card is live shows that card in place of "Plant and ask the lead to fix it", and has no line in Needs you

## Decisions
- **D1. Builds on what is stored already; nothing new.** A plate's plant is an `owner_requests` row (`kind = 'plant'`, the value's `text`), and the runner writes the card it planted in its `result` ("planted <path>", "planted <path>, queued for the lead", "planted already: <path>", `runner/requests.py`). The card's state is in `milestones`. No table, column, setting or job kind is added, so nothing becomes removable.
- **D2. One lookup, in `factory_dashboard/stacks_routes.py`:** `asked_card(conn, project, text_start) -> AskedCard | None`, with `AskedCard(key, title, state, href, on_its_way)`. It takes the project's latest `plant` request whose value's `text` starts with `text_start` (`json_extract(value, '$.text')`):
  - not done and not dismissed → `AskedCard(on_its_way=True)`, other fields empty;
  - done with a result naming a card whose `milestones` row (same project, key = the path's stem) is in a live state (`idea`, `planning`, `ready`, `building`) → that card: `key` is `runner.tasks.short_key` upper-cased ("M13"), `href` is `/planning/<short key>?project=<name>`, `state` is its word (D4);
  - anything else (refused, card done, removed or merged away) → None, and the button is back.
  The stack's `text_start` is `STACK_PLANT.format(name=...)`; the fix's is `f"{name}'s app "`, the head `fix_text` writes.
- **D3. Who carries it.** `ProjectCard.stack_asked` (filled in `project_cards`, only where `stack_plant` is set) and `AppRow.asked` (filled only for a broken app). `row_of` takes the connection as its first argument so every caller fills it the same: `project_cards`, Run, Stop, and the `GET /projects/{name}/app` f284-02 adds.
- **D4. Words.** The label "You asked the lead"; the state words: `idea` and `planning` "being planned", `ready` "ready", `building` "building". On its way, server-drawn: "On its way: the runner plants it and asks the lead at its next pick", the same as the press's line today.
- **D5. Needs you.** A broken app's line is in Needs you only while no fix is asked (`app.needs_you and not app.asked`); `needs_you_count` follows, and the panel goes when nothing is left (owner, 2026-10-02).
- **D6. The picture:** `.softfield/cards/f300-mockup/projects-asked.html`, Proposed. The work order (`.order`) is drawn on the existing tokens (`--bay`, `--rule`, `--stripe`, `--notch`), its CSS in the app row's block of `dashboard.css`; on its way is the dashed `--opus` edge the page already uses. No new colour or shape.
- **D7. Only the factory's own button counts.** A stack or fix card the owner planted by hand, in other words, isn't recognised: the button stays. Matching words would guess; the button is there to save typing, and pressing it again is caught by "planted already".

## Tickets
- f300-01-stack-plate-shows-its-card (developer)
- f300-02-fix-button-shows-its-card (developer)

## Before and after
- `/projects`
