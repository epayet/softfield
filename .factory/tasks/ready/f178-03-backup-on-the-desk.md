---
id: f178-03-backup-on-the-desk
milestone: f178-show-the-backups-on-the-dashboard
difficulty: 3
depends_on: [f178-01-backup-facts]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A failing backup shows first on the Planning desk, in its own group, and its item opens the Backups bay on the Projects page.

### Context
The picture to build is the desk in Proposed's "Failing for an hour" state in `.factory/cards/f178-mockup/backups.html`. Read D5 in `.factory/cards/f178-show-the-backups-on-the-dashboard.md`, then `desk` and `_blocked` in `factory_dashboard/planning.py` (the example: a group read from `owner_items` by kind) and the desk in `factory_dashboard/templates/planning.html`.
- The kind is `ITEM_KIND` in `runner/backup.py`; the item belongs to the project the runner was running.
- The group's key is `backup`, its name "Backup failing", its colour `--fail`; the item's title is "The metrics database's daily copy is failing", its words the item's text, its link `/projects#backups`. It renders through the template's generic item branch; no button.
- `desk`'s docstring counts the groups: keep it true.

### Done when
- an open `backup` item makes a "Backup failing" group, first on the desk, with one item linking to `/projects#backups`, and it counts in the desk's number and in the project's "for you" on the Projects page
- a resolved one shows nothing, and no other group changes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
