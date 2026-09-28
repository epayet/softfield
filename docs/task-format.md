# Task format

Tasks are Markdown files with YAML frontmatter in `tasks/ready/`. Claude writes them; the runner moves them to `done/` or `escalated/`. The file name is `<id>.md`.

## Frontmatter

```yaml
---
id: m1-03-space-reaction-set        # unique; m<milestone>-<nn>-<slug>
milestone: 1
depends_on: [m1-02-space-model]     # task ids; [] if none
files:                              # the ONLY paths the task may change
  - coucou/reactions.py
tests:                              # the tests that define done (already exist, currently failing)
  - tests/unit/test_reactions.py
max_diff: 150                       # added+removed lines, optional (default 150)
finding: m1-F2                      # optional: the review finding this fixes
---
```

## Body sections (all required, in this order)

### Goal
One or two sentences. One concept.

### Context
Everything the model needs, **pasted in**, so it never has to explore:
- the exact signatures, dataclasses, Protocols and constants it calls or implements
- relevant settings names and fixture names
- any rule from an ADR that applies, quoted

The runner's pre-flight checks that every quoted path exists and every quoted `def`/`class` name is found.

### Pattern to follow
One existing file whose style and structure to copy, e.g. `coucou/ordering.py`.

### Steps
Numbered and specific down to function names, e.g. "Implement `validate_reaction_set(emojis: Sequence[str]) -> ReactionSet` raising `InvalidReactionSet` when…".

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

## Sizing rules

- 1–3 files and one concept per task.
- **Keep the spec short** ([ADR 01](adr/01-calibration-fixes.md)): the local model drops instructions from long prompts. Aim for Context ≤ ~60 lines and ≤ 5 short Steps, and paste only what the model calls or implements. Spell out test expectations only where the test file doesn't make them obvious, and put the one crucial instruction last.
- Backtick the full repo path of every file whose signatures you paste (pre-flight searches those files), and never backtick a bare file name.
- **Skeleton first:** Claude commits the stubs (`raise NotImplementedError`) and the failing tests to `main` before the task enters `ready/`.
- If a task needs more than `max_diff`, split it.
- Protected paths never appear in `files:`.
- A task that adds user-facing text lists `coucou/locale/fr/LC_MESSAGES/django.po` and `django.mo` (or `djangojs.*` for JS) in `files:`, and its Steps say which French strings to add.

## Result footer (appended by the runner)

```yaml
# --- runner ---
result: done | escalated
attempts: 2
duration_s: 412
gate_failures: [ruff, tests]
```
