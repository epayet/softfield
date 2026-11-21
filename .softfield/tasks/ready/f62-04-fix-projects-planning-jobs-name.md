---
id: f62-04-fix-projects-planning-jobs-name
milestone: f62-claude-opus-review-on-overview-does
agent: lead
difficulty: 3
depends_on: []
files:
- factory_dashboard/coming.py
tests:
- tests/factory_dashboard/test_projects.py
- tests/factory_dashboard/test_coming.py
- tests/factory_dashboard/test_jobs.py
finding: f275-a-project-created-by-web-interface-C2611-1
---

### Goal
Fix a checkpoint finding on f62-03-projects-planning-jobs-name-the-card: Two ticketless-card naming paths are wrong

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f62-03-projects-planning-jobs-name-the-card.md`. What it found is under Finding:
- f275-a-project-created-by-web-interface-C2611-1, should-fix: in `factory_dashboard/coming.py`, line 474.

### Finding
f275-a-project-created-by-web-interface-C2611-1: Two ticketless-card naming paths are wrong
> The ticket is broken in `coming.py`: `_next_reply` bypasses `_what` for planner jobs (`role in REPLIES`) and therefore a ticketless planner reply does not name its card. Quote Goal: "the Planning room's 'after …' wait ... name the card a ticketless review, planner reply or checkpoint works on." `reply_line` also bypasses `_what` for the ahead planner at line 524. Separately, `factory_dashboard/templates/projects.html:22` builds a running card link using the global `project` context instead of `job.project`, so a live card in another project opens the wrong planning project. Quote Goal: "the key linked to `/planning/f158?project=<project>`."

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
