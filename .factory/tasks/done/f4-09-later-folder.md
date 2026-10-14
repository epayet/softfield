---
id: f4-09-later-folder
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/loop.py
  - runner/cli.py
  - runner/tasks.py
  - docs/task-format.md
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_cli.py
---

### Goal
Tickets in `tasks/later/` wait aside: the runner never takes them, records them as `later`, and `uv run runner queue <ticket>` puts one back in `ready/`.

### Context
Read `docs/adr/17-always-on-factory.md` item 3, `runner/loop.py` (`TICKET_FOLDERS`, `sync_tickets`), `runner/cli.py` (how `signoff` is wired) and `docs/task-format.md`. Test-first.
- `tasks/later/` exists already, with `tasks/later/m4-12-send-recovers.md` (set aside 2026-10-02).
- `sync_tickets` records each folder's tickets with the folder's name as their state, so add `later`.
- `runner queue <ticket>` takes a full id or a unique prefix. It `git mv`s the file to `ready/`, commits "queue <id> (by the owner)" without the hook (tasks-only), and refuses while a run is live (a heartbeat under 2 minutes), as other owner commands do. It also refuses a ticket that isn't in `later/`.
- Add `tasks/later/` to `docs/task-format.md`'s folder list.

### Done when
- `runner run --dry-run` never lists a ticket from `later/`
- `sync_tickets` records a later ticket with state `later`
- `runner queue m4-12` moves m4-12 to `tasks/ready/` and commits; an unknown or ambiguous id prints the choices and changes nothing
- `uv run runner check-all --task f4-09-later-folder` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
