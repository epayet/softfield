# AGENTS.md: rules for every coding agent

These rules apply to Claude and the local model alike. When a task file and this file disagree, stop and write `BLOCKED.md`.

## Scope
1. Change **only** the files listed in your task's `files:`. Nothing else, not even "while I'm here" fixes.
2. Never edit a **protected path** (`workflow/protected-paths.txt`) or an **existing test file**. The gates reject both.
3. Add **no dependencies** (`pyproject.toml`, `uv.lock`, vendored JS) unless the task explicitly says so.
4. Build only against ADRs whose status is **Accepted**. If a task relies on a Proposed ADR, write `BLOCKED.md`.

## Code
5. `coucou/core/` is **pure**: no Django, DB, files, network, clock or randomness. Time and IDs are parameters. Side effects live in `coucou/edges/`. import-linter enforces this.
6. Type-hint everything. Code must pass ruff (lint + format) and mypy.
7. No third-party network calls, CDNs, fonts, analytics or trackers. Every asset is self-hosted.
8. Never log note text or photo contents.
9. Wrap user-facing strings for translation. Keep the tone light and warm.

## Tests
10. Unit tests cover `coucou/core` only. Integration tests use the fakes in `tests/fakes/` or Django's test DB. See `docs/testing.md`.
11. A task is done when its listed `tests:` pass **and** the full unit + integration suite still passes.
12. Don't weaken, skip or delete a test to make it pass.

## When you're stuck: `BLOCKED.md`
Write `BLOCKED.md` at the repo root, then stop. Its first line is exactly one of:
- `CATEGORY: false-assumption`: the spec says something exists or behaves a way it doesn't
- `CATEGORY: needs-file`: you need a file outside `files:` (name it)
- `CATEGORY: needs-info`: you need a fact or decision (ask one precise question)
- `CATEGORY: unrelated-problem`: you noticed an unrelated problem; describe it, then **carry on**

Never ask questions interactively. Nobody is there to answer.

## Discoveries
Unplanned work you notice (a bug, missing test, refactor idea) goes as one bullet in `docs/discoveries.md`, **never** into code.

## What to read
- Any task: the task file and this file. The task's Context should be enough on its own.
- Python/Django: `docs/architecture.md`
- Tests: `docs/testing.md`
- Anything touching devices, auth, uploads or scoping: `docs/security.md` (these are usually protected)
