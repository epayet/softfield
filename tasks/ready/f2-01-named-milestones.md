---
id: f2-01-named-milestones
milestone: f2
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/tasks.py
  - runner/cli.py
  - runner/milestone.py
  - runner/owner.py
  - runner/backfill.py
  - docs/task-format.md
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_milestone.py
  - tests/runner/test_owner.py
  - tests/runner/test_backfill.py
---

### Goal
A milestone can have a descriptive key like `f3-factory-line`, typed in full or as `f3`, while its ticket ids stay short (`f3-01-factory-line`).

### Context
Read `docs/adr/16-claude-window-and-named-milestones.md` item 6 and `docs/milestones/f2.md` D4. Test-first.
- Today a key must fullmatch `_KEY_RE = ([a-z]+)(0|[1-9]\d*)` (`runner/tasks.py`: `milestone_key`, `command_arg`, `_key_parts`, `next_milestone_key`, `milestone_order`); the CLI parses its argument with `milestone_key` (`runner/cli.py`).
- Tickets are found by their id's prefix, `<key>-`: `glob(f"{milestone}-*.md")` in `runner/milestone.py` and `runner/owner.py`, `startswith(f"{milestone}-")` in `runner/owner.py`, `^[a-z]+\d+-\d+-` in `runner/milestone.py`, and `_TICKET_RE`/`_KEY_RE` in `runner/backfill.py`. With a named key, the prefix is the short form (`f3`), not the key.
- Docs are `docs/milestones/<key>.md` and `docs/reviews/<key>.md` (`runner/milestone.py`, `runner/owner.py`, `runner/backfill.py`): use the full key; an existing short-key doc (`docs/milestones/f2.md`, `docs/milestones/m4.md`) still works.
- The command: `uv run runner milestone f3` and `uv run runner milestone f3-factory-line` mean the same milestone when its tickets say `milestone: f3-factory-line`. Both forms in frontmatter resolve to the full key when a doc `docs/milestones/<full key>.md` exists.
- `m1`–`m4`, `f1` and `f2` keep working unchanged (bare numbers too). Sorting stays by series and number.
- `docs/task-format.md` still says the id is ``m<milestone>-<nn>-<slug>``: describe both forms.

### Done when
- `milestone_key("f3-factory-line")` is accepted, `f3` and `f3-factory-line` order the same, and `f-1`, `F3` and `f3-` are still refused
- a milestone keyed `f3-factory-line` finds its `f3-01-…` tickets, its doc and its review, in the runner and in backfill
- every existing test passes unchanged
- `uv run runner check-all --task f2-01-named-milestones` passes
