---
id: f178-01-backup-facts
milestone: f178-show-the-backups-on-the-dashboard
agent: lead
difficulty: 5
depends_on: []
files:
  - runner/backup.py
  - runner/config.py
  - runner/loop.py
tests:
  - tests/runner/test_backup.py
  - tests/runner/test_config.py
---

### Goal
The dashboard can read the backups (the machine's `[backup]` settings and each copy's time and size), and copies that keep failing for an hour put an item on the owner's desk that clears itself when one works.

### Context
Read D2 and D4 in `.softfield/cards/f178-show-the-backups-on-the-dashboard.md`, then `runner/backup.py` (`copies`, `taken_at`, `Backups`, `RETRY_AFTER`), `machine_ntfy` and `_backup` in `runner/config.py`, and in `runner/loop.py` `check_backup`, `_resolve_items`, `_notify` and the `upsert_owner_item` call in `run_planner` as the example of an item the runner opens.
- `listing(folder)` returns `Copy(path, taken, size)` oldest first; missing folder → `[]`; a file gone before its `stat` (pruned by a running copy while the dashboard lists) is skipped.
- `machine_backup()` reads only the machine file, like `machine_ntfy`, through `_backup`.
- `ITEM_KIND = "backup"` lives in `runner/backup.py`; the item's subject is `metrics`, its text one plain sentence: "The metrics database's daily copy has failed since <d Mon HH:MM>: <Type>: <error>. The runner tries again every 5 minutes; this clears by itself when one works."
- The session remembers when the failures began (the first failure since the last copy that worked); the existing once-per-stretch report note stays.
- On a copy that works, resolve open `backup` items in every project (the copies are the machine's), not only the running one.

### Done when
- `listing` gives each copy's time and size in bytes, oldest first, ignores other files and `.part` files, and is `[]` for a missing folder
- `machine_backup()` gives the machine file's `[backup]`, the defaults without one, and `ConfigError` for a bad `keep`
- failures for less than an hour open no item; once they have lasted an hour, one `backup` item is open on the running project with the error in its text, and one notification is sent; further failures update its text and send nothing more
- the next copy that works resolves the open `backup` items of every project
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
