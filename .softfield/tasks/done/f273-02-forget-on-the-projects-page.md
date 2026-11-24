---
id: f273-02-forget-on-the-projects-page
milestone: f273-i-need-the-ability-to-forget
difficulty: 2
depends_on: [f273-01-forget-request, f262-02-archive-on-the-projects-page]
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
Each project in the Projects page's Archived bay has a Forget button that asks once, on the page, then posts the request and shows it on its way.

### Context
The picture to build: the Proposed side of `.softfield/cards/f273-mockup/projects.html`. Read D4 and D5 in `.softfield/cards/f273-i-need-the-ability-to-forget.md`.
- The Archived bay and its Unarchive button are f262-02's, in `project_cards` (`factory_dashboard/projects.py`) and `factory_dashboard/templates/projects.html`: Forget is posted and shown on its way the same way, with the kind `forget_project` and the row's project as `project`.
- The question opens on the page, with no browser pop-up; "Keep it" closes it and posts nothing.
- A project's app row (Running, Stop, Logs) is `factory_dashboard/templates/_partials/app_row.html`, already drawn on the listed plates.
- The question's stripe is the hazard stripe (`--stripe`); no status colour on ornament (owner.md, "Factory theme"); any new colour joins the tokens at the top of `dashboard.css` first.

### Done when
- each archived project's crate has Forget beside Unarchive, quieter than Unarchive
- pressing Forget opens, under the crate, "Forget <name>?" with what leaves, that nothing is deleted, the project's folder, that `softfield init` in that folder brings it back, the count of its open items for the owner when there are any, and "Yes, forget it" / "Keep it"
- "Yes, forget it" posts `forget_project`; Forget turns "Forgetting…", dashed orange and disabled, with "On its way: the runner takes it at its next pick, after the job it is on", at once and after a reload while the request is open
- an archived project whose app runs shows its app row in its crate, and Forget is disabled with "Its app is running: stop it first, then Forget."
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 14708475
logs: .softfield/var/runs/20261124-131732/f273-02-forget-on-the-projects-page
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
