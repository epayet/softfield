---
id: f127-02-who-reads-what
milestone: f127-shared-rules-stay-shared-across-projects
difficulty: 3
depends_on: []
agent: lead
files:
  - factory_dashboard/projects.py
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
The Projects page lists, for each project and role, the files a job gets: from Softfield with the date each last changed, yours, or this project's (ADR 41 item 6).

### Context
Read ADR 41 items 4 and 6 in `.softfield/adr/41-the-factory-is-optional.md`. This changes a page, so the lead draws a mock-up first (Today and Proposed, in the factory theme) and the owner approves it before this is queued.

### Done when
- each role's files show with where they come from, and a machine file replacing the author's shows as yours
- the listed `tests:` pass, and fail without the change
