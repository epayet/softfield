# Milestone F136: softfield init asks what to do with a forgotten project of the same name

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
if i forgot about a projject with softfield forget, and i init with a project with a name where there was already data before, i want to be asked whether i use previously used factory data (continue on the same one), keep the old and make a new entry (like -1). yeet the old data and make a brand new. i had an issue in my tests where i reused the same previously used project name, the lead made a m1 ticket, which already existed and on the board when i wanted to archive it, it archived both, seems like clashes were not handled well

## Plan (lead, 2026-10-27)
- **What happened, from the database:** `softfield forget` only marks the project's row `forgotten` (`_forget`, `runner/cli.py`); its cards, tickets, threads and runs stay under the same project id. `softfield init` in a new folder of the same name then calls `upsert_project` (`setup.register`), which finds that row again, takes it back and sets it `setting up`. The new project lives on top of the old one's data. test-factory-hello (id 3) holds both lives today: `m1-hello-and-happy-birthday` (the old card, its doc gone with the old folder) and `m1-uv-run-hi` (the new one).
- **Why archiving took both:** a thread is keyed by a card's short key (`m1`), and so is the runner's clean-up of cards whose doc is gone (`sync_cards` in `runner/loop.py` passes short keys to `metrics.remove_cards`). The new `m1-uv-run-hi.md` made `m1` "present", so the old card never left the board, and both cards shared the one `m1` thread: archiving it archived both.
- **Worse, unasked:** `init` in a folder named like a project that is still live elsewhere (two folders called `hello`) takes that project's row too and points it at the new folder.
- Tickets, all lead (`runner/**` is protected): `f136-01-gone-card-leaves-the-board`, `f136-02-init-asks-about-the-old-entry`, `f136-03-start-fresh-wipes-the-old-entry` (waits for 02).
- No mock-up: everything here is in the terminal (`softfield init`'s question); no page changes.

## Decisions
- **D1: `init` looks for the name before it writes anything.** A row named like the folder, forgotten or not, means a choice; with none, `init` goes on as today.
- **D2: the choices.**
  - **Continue** (the old entry comes back with its history): offered only when the folder still holds that project, i.e. its `.factory/project.toml` names it and the row is forgotten. `init` then writes nothing, un-forgets the row (`setting up`, as a new one) and points it at this folder; `softfield doctor` hands it over as usual. Not offered for a folder without the old files: its new cards would start at M1 again and land on the old M1's thread, the clash seen in the tests.
  - **Keep the old, start a new one** (the default): the old row is renamed `<name>-1` (`-2`, … the first free), keeps its history and stays forgotten; the new project takes the folder's name. The old one is renamed rather than the new one, because the folder name is what `project.toml`, the dashboard's `?project=` and the hand-over use.
  - **Start fresh**: the old row and everything under it is deleted (D3), after the owner types the project's name.
  - A row that is **live** (not forgotten) offers only "keep": the new project is named `<name>-2` (the first free) in its `project.toml`, and the live one is untouched. Never two live projects under one name.
- **D3: what "start fresh" deletes:** every row under the project id: `milestones`, `tickets`, `runs` and their `jobs`, `findings`, `owner_items`, `owner_requests`, `work_queue`, `planner_threads` and their `planner_messages`, then the `projects` row, in one transaction. Machine-wide rows stay: `usage_events`, and `rating_changes` (the agents' ratings) with their `ticket_id` set to NULL. The daily Dropbox backup still holds what was deleted until it rolls over.
- **D4: no terminal, no guess.** `softfield init --previous continue|keep|fresh` answers without a question (`fresh` still needs `--yes`); without a terminal and without the flag, `init` stops and names the three.
- **D5: a card whose doc is gone leaves the board even when a new doc shares its short key.** `sync_cards` (and `setup.publish_cards`) remove the project's card rows whose full key no doc in `.factory/cards/` has, where another doc has the same short key. A row whose short key no doc has is removed as today. Card docs are never renamed (a lead's naming rewrites only the heading), so a full key is stable.
