---
id: f1-16-developer-rename
milestone: f1
depends_on: [f1-15-agents-page]
agent: lead
difficulty: 5
files:
  - AGENTS.md
  - CLAUDE.md
  - docs/agents/developer.md
  - docs/agents/lead.md
  - docs/task-format.md
  - docs/task-writing.md
  - docs/workflow.md
  - runner/tasks.py
  - runner/prompts.py
  - runner/loop.py
  - runner/report.py
  - opencode.json
  - docs/how-it-works.md
  - tests/browser/test_delivery.py
  - tests/runner/test_config.py
  - tests/runner/test_loop.py
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_prompts.py
---

### Goal
"Junior" becomes "developer" everywhere it names a role (ADR 14 item 1), and `docs/agents/junior.md` becomes `docs/agents/developer.md`.

### Context
Read `docs/adr/14-developers-and-agents.md` item 1. Find every use with `Grep` (`junior`, case-insensitive) outside `docs/sessions/`, `docs/reviews/` and `tasks/done/`, which are history and stay as written; so are `docs/adr/` and the docs of finished milestones (`docs/milestones/m*.md`, `docs/milestones/f1-mockup.html`).
- Facts (f1-07): besides the files above, `docs/agents/junior.md` is named in `tests/runner/test_config.py` (the protected-tests list), `docs/how-it-works.md` and `tests/browser/test_delivery.py`; "junior" as a role also appears in comments in `runner/checks.py`, `runner/state.py`, `runner/local_model.py`, `runner/gates.py`, `runner/gitops.py`, `workflow/runner.toml` and `workflow/protected-paths.txt`. The loop's checkpoint counts merges of `task.agent == "junior"` tickets (`runner/loop.py`). The database already says `developer` (tickets' `kind`, jobs' `role`).
- **Tickets:** `agent: developer` is the default; `agent: junior` is still accepted, as a synonym (`runner/tasks.py`). Records and the database say `developer`.
- **The rename:** `git mv` isn't available to you; create `docs/agents/developer.md` with the same content and delete the old file. Update every reference: `opencode.json`'s instructions, the checkpoint's `Edit(docs/agents/junior.md)` rule in `runner/loop.py`, the prompts, lead.md's budget line, CLAUDE.md, and the tickets still in `tasks/ready/`.
- Test names and fixtures that mean the role follow; test names that record history ("m4-06's junior") may stay.

### Done when
- a ticket with no `agent:`, with `agent: developer` and with `agent: junior` all parse as `developer`
- no prompt the runner builds says "junior"
- `docs/agents/junior.md` is gone and nothing outside history refers to it (a test greps the runner's source and `opencode.json`)
- `uv run runner check-all --task f1-16-developer-rename` passes

```yaml
# --- runner ---
result: blocked
reason: check-all failed; the work is on task/f1-16-developer-rename
```

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: finished by the lead interactively: git rm docs/agents/junior.md (the headless job had no rm rule)
```
