# AGENTS.md: rules for every coding agent

**Who are you?**
- **Developer** (running a task from `.factory/tasks/`): this file plus `docs/agents/developer.md` (both are in your prompt already).
- **Lead** (planning, writing tickets, escalations, review): this file plus `docs/agents/owner.md` (the owner's preferences, first) and `docs/agents/lead.md`.

When a task file and this file disagree, stop and write `BLOCKED.md`.

## Scope
1. Start from your task's `files:` and `tests:`. Change other files only when the goal needs it, and no "while I'm here" fixes.
2. Never edit a **protected path** (`.factory/protected-paths.txt`). The gates reject it.
3. Add **no dependencies** (`pyproject.toml`, `uv.lock`, vendored JS) unless the task explicitly says so.
4. Build only against ADRs whose status is **Accepted**. If a task relies on a Proposed ADR, write `BLOCKED.md`.

## Code
5. Keep rules as plain functions without side effects where practical: time and paths are parameters; git, SQLite, subprocesses and HTTP stay at the edges (`runner/loop.py`, `runner/gitops.py`, `runner/metrics.py`, the dashboard's routes).
6. Type-hint everything. Code must pass ruff (lint + format) and mypy.
7. No third-party network calls, CDNs, fonts, analytics or trackers in the dashboard. Every asset is self-hosted (`factory_dashboard/static/vendor/`).
8. The dashboard writes only through `POST /requests` (ADR 18); the runner is git's one writer.

## Tests
9. **One test file per module:** `runner/<name>.py` → `tests/runner/test_<name>.py`, `factory_dashboard/<name>.py` → `tests/factory_dashboard/test_<name>.py`. Add to the existing file; never create a second one. Tests use temporary git repos and databases, never the real ones.
10. Write tests for what the task's "Done when" asks. They must fail without your change and pass with it.
11. Change an existing test only when the task changes that behaviour. Never skip, xfail or delete a test to make it pass.
12. A task is done when its `tests:` pass **and** the full suite still passes (`softfield check-all`).

## When you're stuck: `BLOCKED.md`
Write `BLOCKED.md` at the repo root, then stop. Its first line is exactly one of:
- `CATEGORY: false-assumption`: the spec says something exists or behaves a way it doesn't
- `CATEGORY: needs-file`: you need to change a protected file (name it)
- `CATEGORY: needs-info`: you need a fact or decision (ask one precise question)
- `CATEGORY: unrelated-problem`: you noticed an unrelated problem; describe it, then **carry on**

Never ask questions interactively. Nobody is there to answer.

## Discoveries
Unplanned work you notice (a bug, missing test, refactor idea) goes as one bullet in `docs/discoveries.md`, **never** into code.

## What to read
- Any task: the task file, the files it points to, and the worked example it names.
- How the factory works: `docs/how-it-works.md` and `docs/workflow.md`; tickets: `docs/task-format.md`.
