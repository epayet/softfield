---
id: f149-02-backlog-items-to-seeds
milestone: f149-is-docs-backlog-md-still-used
difficulty: 3
depends_on: [f149-01-reviews-stop-writing-a-backlog]
agent: lead
commands: [rm docs/backlog.md]
files:
  - docs/backlog.md
  - .factory/tasks/later/
  - .factory/cards/
tests:
  - tests/runner/test_tasks.py
---

### Goal
Softfield's `docs/backlog.md` is gone: each item it held worth keeping is a bug seed on the board or a planted card, and the rest are named as dropped with their reason.

### Context
Read `.factory/cards/f149-is-docs-backlog-md-still-used.md`, D3 and D4: D4 decides every item, by its source tag in `docs/backlog.md`. Check each against the code first: one already fixed is dropped as done.
- A bug seed: shaped like `.factory/tasks/later/bug-43-remove-the-dead-line-page.md`, the next free `bug-<nn>` after the highest in `.factory/tasks/*/`, `finding:` the item's source, no `priority:`, the item's words and fix carried in full (the file is going).
- A planted card: shaped like a seed card the runner writes, for example `.factory/cards/f163-give-developers-a-browser-level-check.md`: the title line, `> **State:** idea · **Priority:** 100 · **Area:** factory`, a line "From docs/backlog.md (f53-review), written by the lead on <date>.", then `## Notes` with the item's words in full. Its key is the next free `f` number (`next_key` in `runner/planner.py`). Read the cards whose state is idea or ready first: when one covers the item, add it to that card's Notes instead.
- Delete the file with `rm docs/backlog.md` (a headless job can't delete one otherwise), then grep the repo, `.factory/` aside, for `backlog.md` and fix any link left.

### Done when
- `docs/backlog.md` is deleted, and no file outside `.factory/reviews/`, `.factory/sessions/` and `.factory/tasks/done/` links to it
- each D4 bug seed is a ticket in `.factory/tasks/later/` that passes `softfield check-tickets`, and each D4 card is a new card or a line in an existing card's Notes
- the job's note lists every item of the file with where it went: a bug ticket, a card (its key), or dropped and why
- `uv run pytest -q tests/runner/test_tasks.py` passes
- all gates pass (see `docs/workflow.md`)
