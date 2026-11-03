# The factory's rules, for every developer it starts

A project's `.softfield/project.md` overrides any of them, except a rule a gate enforces: that one changes in `.softfield/project.toml` or `.softfield/protected-paths.txt`.

When a task file and these rules disagree, stop and write `BLOCKED.md`.

## Scope
1. Start from your task's `files:` and `tests:`. Change other files only when the goal needs it, and no "while I'm here" fixes.
2. Never edit a **protected path** (`.softfield/protected-paths.txt`). The gates reject it.
3. Add **no dependencies** unless the task explicitly says so.
4. Build only against ADRs whose status is **Accepted** (`.softfield/adr/`). If a task relies on a Proposed ADR, write `BLOCKED.md`.

## Code and tests
5. The project's own code rules are in `.softfield/project.md`.
6. Write tests for what the task's "Done when" asks. They must fail without your change and pass with it.
7. Change an existing test only when the task changes that behaviour. Never skip, xfail or delete a test to make it pass.
8. A task is done when its `tests:` pass **and** `softfield check-all` passes.

## When you're stuck: `BLOCKED.md`
Write `BLOCKED.md` at the repo root, then stop. Its first line is exactly one of:
- `CATEGORY: false-assumption`: the spec says something exists or behaves a way it doesn't
- `CATEGORY: needs-file`: you need to change a protected file (name it)
- `CATEGORY: needs-info`: you need a fact or decision (ask one precise question)
- `CATEGORY: unrelated-problem`: you noticed an unrelated problem; describe it, then **carry on**

Never ask questions interactively. Nobody is there to answer.

## Discoveries
Unplanned work you notice (a bug, missing test, refactor idea) goes as one bullet in `.softfield/discoveries.md`, **never** into code.
