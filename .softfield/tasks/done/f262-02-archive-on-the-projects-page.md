---
id: f262-02-archive-on-the-projects-page
milestone: f262-i-want-ability-to-archive-a
difficulty: 3
depends_on: [f262-01-archive-a-project, f124-02-pause-on-the-projects-page]
files:
  - factory_dashboard/app.py
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
  - tests/factory_dashboard/test_app.py
---

### Goal
An archived project leaves the project picker, the top bar's status and the Projects page's list, and sits in a folded Archived bay under the list; each project has an Archive button and each archived one an Unarchive, shown on their way at once.

### Context
The picture to build: the Proposed side of `.softfield/cards/f262-mockup/projects.html`. Read D4, D5 and D7 in `.softfield/cards/f262-i-want-ability-to-archive-a.md`.
- The picker's names are built in `page` in `factory_dashboard/app.py` (keep its rule that the page's own project shows, last, when it isn't listed); the top bar's status in `factory_wide_status` in the same file.
- The Projects page is `project_cards` in `factory_dashboard/projects.py` and `factory_dashboard/templates/projects.html`; f124-02 put a Pause / Resume button there that asks the runner: Archive and Unarchive are posted and shown on their way the same way, with the kinds `archive_project` and `unarchive_project` and the row's project as `project`.
- `metrics.is_archived(row)` in `runner/metrics.py` says whether a project is archived.
- The bay's stripe and edges use the rules and ink, never a status colour (owner.md, "Factory theme"); any new colour joins the tokens at the top of `dashboard.css` first.

### Done when
- an archived project is not in the picker, unless the page is its own (then last and selected, as today); `factory_wide_status` ignores it
- the Projects page's ordered list and order form leave it out; under the list, a closed `<details>` "Archived · N" lists each archived project with its description, "Archived by you", its ready and done counts, Planning and Board links and Unarchive; with none archived, no bay
- each listed project not being set up has Archive at the foot of its plate; pressing Archive or Unarchive turns it "Archiving…" or "Unarchiving…", dashed orange and disabled, with "On its way: the runner takes it at its next pick, after the job it is on", before the answer comes, and after a reload while the request is open
- Needs you on the Projects page still lists an archived project's items
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 5354993
logs: .softfield/var/runs/20261124-131732/f262-02-archive-on-the-projects-page
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
