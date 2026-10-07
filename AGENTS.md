# AGENTS.md: rules for every coding agent

**Who are you?**
- **Developer** (running a task from `tasks/`): this file plus `docs/agents/developer.md` (both are in your prompt already).
- **Lead** (planning, writing tickets, escalations, review): this file plus `docs/agents/owner.md` (the owner's preferences, first) and `docs/agents/lead.md`.

When a task file and this file disagree, stop and write `BLOCKED.md`.

## Scope
1. Start from your task's `files:` and `tests:`. Change other files only when the goal needs it, and no "while I'm here" fixes.
2. Never edit a **protected path** (`workflow/protected-paths.txt`). The gates reject it.
3. Add **no dependencies** (`pyproject.toml`, `uv.lock`, vendored JS) unless the task explicitly says so.
4. Build only against ADRs whose status is **Accepted**. If a task relies on a Proposed ADR, write `BLOCKED.md`.

## Code
5. Write business rules as plain functions without side effects where practical: time and IDs are parameters, and Django, DB and IO stay in `models/`, `views/`, `repos.py` and friends.
6. Type-hint everything. Code must pass ruff (lint + format) and mypy.
7. No third-party network calls, CDNs, fonts, analytics or trackers. Every asset is self-hosted.
8. Never log note text or photo contents.
9. **English and French:** wrap every user-facing string (`gettext`, `{% translate %}`, JS `gettext()`), and add its French translation to `coucou/locale/fr/LC_MESSAGES/` in the same task, with all its accents (é, è, à, ç…), then compile it: `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po` (JS strings: the same with `djangojs.po` and `djangojs.mo`). API errors use stable codes, not sentences. Admin-only text stays plain English. Keep the tone light and warm in both languages.

## Tests
10. **One test file per module:** `coucou/<name>.py` → `tests/unit/test_<name>.py`, `coucou/static/coucou/js/<name>.js` → `tests/browser/test_<name>.py`. Add to the existing file; never create a second one. Unit tests don't touch Django; integration tests use `tests/fakes/` or Django's test DB. See `docs/testing.md`.
11. Write tests for what the task's "Done when" asks. They must fail without your change and pass with it.
12. Change an existing test only when the task changes that behaviour. Never skip, xfail or delete a test to make it pass.
13. A task is done when its `tests:` pass **and** the full unit + integration suite still passes.

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
- Python/Django: `docs/architecture.md`. Tests: `docs/testing.md`.
- Anything touching devices, auth, uploads or scoping: `docs/security.md` (these are usually protected).
