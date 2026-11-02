---
id: f178-02-backups-panel
milestone: f178-show-the-backups-on-the-dashboard
difficulty: 4
depends_on: [f178-01-backup-facts]
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
The Projects page has a Backups bay under Projects: how many copies against the cap, their total size, when the last was taken and the next is due, and a shelf with a crate per copy.

### Context
The picture to build is Proposed in `.softfield/cards/f178-mockup/backups.html` (its three states). Read D1 and D3 in `.softfield/cards/f178-show-the-backups-on-the-dashboard.md`, then `projects_page` and `project_cards` in `factory_dashboard/projects.py`, `factory_dashboard/templates/projects.html` and the Projects page's rules in `factory_dashboard/static/dashboard.css`.
- The facts come from `machine_backup` in `runner/config.py` and `listing` in `runner/backup.py`; the open failure is the open owner item of kind `ITEM_KIND` (`runner/backup.py`) in any project, read from `owner_items`.
- Times are shown in local time like the rest of the page ("28 Oct 23:05", "20 h ago"); sizes in MB or GB, one decimal at most.
- The bay is `<section id="backups" class="panel">`. New shapes (the shelf, the crates) join the page's rules in `dashboard.css` using its tokens; the crates use the ink and rules only, and `--fail` appears only on a failure line.
- Tapping a crate says when that copy was taken and its size, in a line under the shelf (a few lines of script in the template, as the order form's is).

### Done when
- with copies in the folder, the bay shows their count "of <keep> kept", total and mean size, the newest's time and age, and the next copy's time (`every_hours` after the newest)
- the shelf has one crate per copy, oldest first, and dashed empty slots up to `keep`
- with an open `backup` item, a failure line shows its text above the facts; with none and the newest copy older than `every_hours` plus an hour, a calm "No copy for …" line shows instead
- no folder or no copies: the bay says no copy has been taken yet; a bad `[backup]` table: the bay shows the error's text, and the rest of the page still renders
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
