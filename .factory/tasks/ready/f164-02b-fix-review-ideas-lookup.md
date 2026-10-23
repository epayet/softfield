---
id: f164-02b-fix-review-ideas-lookup
milestone: f164-i-like-reading-the-milestone-reviews
difficulty: 3
depends_on: []
finding: f164-02 review_ideas never finds the factory's project, and matches one plant request per project
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
`review_ideas` plants a factory idea in the project whose folder holds the factory's code, and gives every idea its own state, not only the latest plant's.

### Context
Facts from reading `review_ideas` and `_factory_project` in `factory_dashboard/milestones.py` (f164-02):
- `_factory_project` selects `projects` rows `WHERE name = ?` with the review's own name, so it can only ever look at the review's own project and returns its name; a second project whose folder holds `runner/loop.py` and `factory_dashboard/app.py` is never found. The test `test_a_factory_idea_plants_in_the_factory_s_own_project` only checks the fallback (project == PROJECT), so it passes whatever the lookup does.
- Plant requests are read only for the review's own `project_id`, but a factory idea plants in another project, so its request (stored on that project) is never seen and the idea stays "plant".
- `latest_per_project` keeps one request per project (`ORDER BY id DESC`, first wins), and each idea is matched against that one only: a review with two planted ideas shows the older one as "plant". It is also keyed by both project names and `str(project_id)` in one dict.
- No test covers "on its way" (`done` NULL) or the id-less ideas of two plants in one project.
- Follow `_repo` in `factory_dashboard/planning.py` to read a project's folder.

### Done when
- with two projects registered, one whose folder holds `runner/loop.py` and `factory_dashboard/app.py`, a factory idea from the other project's review has that project's name; with none, the review's own
- a factory idea whose plant request is stored on the factory's project shows its state (planted, on its way or refused) from the review's page
- two ideas of one review, each with its own plant request in the same project, each show their own state
- an idea whose request has `from` equal to its id and `done` NULL is "on its way" (a test)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
