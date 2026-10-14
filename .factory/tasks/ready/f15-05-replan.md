---
id: f15-05-replan
milestone: f15-reprioritising-tickets
difficulty: 3
depends_on: [f15-04-drag-and-send]
agent: lead
files:
  - .factory/cards/f15-reprioritising-tickets.md
  - .factory/tasks/ready/f15-06-card-actions.md
  - .factory/tasks/ready/f15-07-arrows-go.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
F15's decisions and its last two tickets match what f15-01 to f15-04 built.

### Context
Read `.factory/cards/f15-reprioritising-tickets.md`, the four merged tickets' commits (`git log`), `factory_dashboard/board.py`, `factory_dashboard/templates/board.html`, `factory_dashboard/static/board.js`, and the two tickets in `files:`. ADR 16 item 7: a replan after a chain of lead tickets later tickets rely on.
- Check every fact in the two tickets against the code: the ⋯ menu's markup and ids, where the stage of a card is known, the names in `factory_dashboard/static/board.js`, the tests they tell the developer to follow.
- Fix the tickets and the card's Decisions where they differ, and log what changed under "## Replan" in the card's doc, with a suggested fix for anything seen and not changed.

### Done when
- each of the two tickets names only files, functions, ids and tests that exist on main
- the card's doc has a "## Replan" section dated today
- `uv run pytest -q tests/runner/test_tasks.py` passes
- all gates pass (see `docs/workflow.md`)
