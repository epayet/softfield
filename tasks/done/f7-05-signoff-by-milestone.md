---
id: f7-05-signoff-by-milestone
milestone: f7-factory-fixes
depends_on: []
agent: lead
difficulty: 2
files:
  - runner/owner.py
tests:
  - tests/runner/test_owner.py
---

### Goal
`runner signoff` counts the tickets left in a milestone by their `milestone:` field, not their id prefix.

### Context
Read `_ids` and `signoff` in `runner/owner.py`, and `split_frontmatter` and `short_key` in `runner/tasks.py`. Test-first.
- `_ids` globs `<short key>-*.md`. On 2026-10-04, `f3-08-field-cards` (moved to F5, `milestone: f5-board`) blocked F3's sign-off, which took `--force`; and a ticket re-homed to another milestone keeps its old id (F9 re-homes f3-25, f3-28, f3-29).
- A ticket counts for the milestone its frontmatter names, in either key form (`f3` or `f3-factory-line`).

### Done when
- a ticket with id `f3-…` and `milestone: f5-board` in `ready/` doesn't block F3's sign-off, and does block F5's
- `uv run runner check-all --task f7-05-signoff-by-milestone` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
