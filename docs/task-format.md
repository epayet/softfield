# Task format

Tasks ("tickets") are Markdown files with YAML frontmatter in `tasks/ready/`. The lead writes them; the runner moves them to `done/`, `escalated/` (waiting for the lead) or `blocked/` (past its limits, or waiting for the owner; see the verdict). The file name is `<id>.md`. Why they look like this: [ADR 07](adr/07-spend-less-frontier.md).

## Frontmatter

```yaml
---
id: m4-03-compose-screen            # unique; <short key>-<nn>-<slug> (see "Milestone keys")
milestone: 4                        # the key in either form: 4 (m4), f2, f3-factory-line or f3
difficulty: 5                       # 1 to 10, from the rubric in task-writing.md (ADR 14 item 5)
depends_on: [m4-01-upload-api]      # task ids; [] if none
files:                              # where to work (a pointer, not a limit); may be new files
  - coucou/templates/coucou/compose.html
  - coucou/static/coucou/css/compose.css
tests:                              # the tests that define done; the developer writes or extends them
  - tests/integration/test_compose_page.py
finding: m4-F2                      # optional: the review finding this fixes
agent: lead                         # optional: `lead` for the lead's own tickets (default
                                    # `developer`; old tickets' `junior` means the same)
commands: [ollama list, gh api]     # optional, lead tickets only: extra Bash prefixes for its
                                    # headless job (never git, the owner's commands or the loop)
difficulty_corrected: 7             # optional: set by the lead at review when `difficulty` was off
---
```

`max_diff` is optional and rarely needed: the default is a 1000-line backstop against a rewritten file (`workflow/runner.toml`), not a sizing tool.

### Milestone keys
A milestone key is `<series><n>`, optionally with a slug: `<series><n>-<slug>` ([ADR 16](adr/16-claude-window-and-named-milestones.md) item 6).
- **Short form:** `m4`, `f2` (a bare number `4` means `m4`). Milestones planned before ADR 16 keep it.
- **Full form:** `f3-factory-line`, `m5-history`. The slug is a few lowercase words joined by `-`, starting with a letter, short enough to type.
- **Ticket ids always use the short form:** `f3-01-factory-line`, never `f3-factory-line-01-…`.
- **Docs use the full key:** `docs/milestones/<full key>.md` and `docs/reviews/<full key>.md`. An existing short-key doc (`docs/milestones/f2.md`) still works.
- **Frontmatter and commands take either form:** `uv run runner milestone f3` and `uv run runner milestone f3-factory-line` run the same milestone. `f3` resolves to the full key from `docs/milestones/<full key>.md`, or else from a ticket whose frontmatter names it. Write the full key in frontmatter.
- **Tags use the key as resolved:** `f3-factory-line-start` and `f3-factory-line-done`.

## Body

### Goal (required)
One or two sentences. One concept.

### Context (required)
The files to read, as full repo paths in backticks, and only the facts no file holds (a decision from the milestone's Decisions section, an API shape the lead's code doesn't show yet). Name the worked example to follow. No pasted code, no background "for completeness".

The runner's pre-flight checks that every backticked path exists (or is listed in `files:`), and that every `def`/`class` named in Context is found.

### Done when (required)
Acceptance criteria as bullets: what a user or a caller sees, including the edges. The developer turns each into a test. Then the standing ones:
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

The prompt already ends with `uv run runner check-all --fix --task <id>`, which runs every check; don't repeat finish commands in the ticket.

### Pattern to follow, Steps (optional)
Only when a ticket really needs them: a pattern with no entry in `docs/agents/developer.md`, or a trap the developer would fall into.

## Rules
- **One concept per ticket,** touching as many files as it needs.
- **Short:** Context ≤ ~30 lines. Developers drop instructions from long prompts ([ADR 01](adr/01-calibration-fixes.md)); put the one crucial instruction last.
- Backtick full repo paths only, never a bare file name.
- Protected paths never appear in `files:`: that work is the lead's.
- A ticket that adds user-facing text lists `coucou/locale/fr/LC_MESSAGES/django.po` and `django.mo` (or `djangojs.*` for JS) in `files:`.
- **Security or protected work** keeps the old way: the lead writes the failing tests on main first, and lists them in `tests:`.

## Result footer (appended by the runner)

```yaml
# --- runner ---
result: done | escalated
attempts: 2
duration_s: 412
gate_failures: [ruff, tests]
```
