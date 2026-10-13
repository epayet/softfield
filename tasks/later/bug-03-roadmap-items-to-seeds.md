---
id: bug-03-roadmap-items-to-seeds
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 90
files:
  - docs/milestones/
tests:
  - tests/runner/test_tasks.py
---

### Goal
Every idea the old roadmap still held is either a seed card the owner can see in the Planning room, or is named as already built or already a card, so nothing from it lives only in git history.

### Context
The owner removed the roadmap file on 2026-10-13 (commit `f90e764`): nothing on the dashboard showed it. Its last version is in git: run `git show 483e5a3:docs/roadmap.md` and read all of it. Not a bug: `bugs` is the only key a ticket outside a card can use, and the owner asked for this as a ticket (2026-10-13).
- The lead's first pass that night found 21 open items, listed below with the heading each would take. It was judged from the roadmap's own notes and the card titles, **not from the code: check each against the code, the cards in `docs/milestones/` and the tickets in `tasks/` before writing a card**, and merge an item into an existing card's Notes when one already covers it.
- A seed card is a file in `docs/milestones/` shaped like `docs/milestones/f113-would-a-design-system-help-or.md`: the title line, the State line (`idea`, priority 100, its area), a line saying where it came from ("From the roadmap, written by the lead on <date>."), then `## Notes` with the idea's words and its open questions, copied from the roadmap in full (not a pointer to git). Keys: the next free `f` number for factory, the next free `m` number for product (`next_key` in `runner/planner.py`), one after another.
- Factory items: a command to plant from the terminal (the dashboard takes a plant only from its own page), with the planner's `roadmap` outcome in `runner/planner.py` and `runner/prompts.py` renamed or removed; a running job says which part it is in (planted by the owner on 2026-10-13: find its card, don't write a second); review ADR 23 (parallel developers, cloud and local at once, a second computer with Qwen 9B); which cloud developers come back (the clean bench, `tasks/later/f4-13-sonnet-step-up.md`, Copilot as stand-in, spreading work among equals); the free-tier survey and the monthly offers watch; whether another agent can escalate when Opus is limited; a failed check sent back within the attempt; every attempt's diff and before/after screenshots on a job page; ADRs on the dashboard; the project's README on its page; a workflow page drawn live from `docs/how-it-works.md`; a preview of the work ahead; a bigger map of the line and "what clogged it" computed; a public factory page and widgets; `factory init` for any project (`docs/adr/02-software-factory.md`); research on other software factories (Ramp's Inspect, Linear); Claude suggests features with spare capacity, and a live chat only if threads feel too slow.
- Product items (product work is on hold: cards only, state `idea`, area product): what comes after the MVP (the roadmap's first list, with "what sets Coucou apart"); avatars hanging out together; memory drift; frame displays and the duck key (keep the device choice, the constraints and the comparison page's link); phone widgets.
- Judged already built or already a card, to confirm in one line each: the always-on queue, the dashboard asking the owner, the board, the planning room, seeds and the field, the dashboard fixes of 2026-10-02, Redis (decided no), slow `check-all` (F71), crates (F10), notifications (F12, F114), reordering (F15), the logo (F68), the "stopped" failures (F93), the set-aside tickets in `tasks/later/`.

### Done when
- each open item is a seed card in `docs/milestones/` in the shape above, or is added to the Notes of the existing card that covers it; no two cards hold the same idea
- nothing but cards in `docs/milestones/` changes: the report below goes in the job's note, not in a file
- the job's note lists every roadmap section with where it went: a new card (its key), an existing card (its key), or built (the file or ticket that shows it)
- no card for an item the code shows is built
- `uv run pytest -q tests/runner/test_tasks.py` passes
- all gates pass (see `docs/workflow.md`)
