---
id: f164-02-review-ideas-and-their-state
milestone: f164-i-like-reading-the-milestone-reviews
difficulty: 4
depends_on: []
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The dashboard reads a review's ideas from its stored sign-off sheet, each with its area, the project it plants in and whether it is planted, on its way or refused.

### Context
Read `.softfield/cards/f164-i-like-reading-the-milestone-reviews.md` (D2, D3) and the mock-up the next ticket builds on these, `.softfield/cards/f164-mockup/review-ideas.html`.
- Add `review_ideas(conn, project, key)` to `factory_dashboard/milestones.py` and a frozen dataclass for one idea: `id`, `text`, `area`, `project` (where it plants), `state` ("plant", "on its way", "planted", "refused"), `card` (the planted card's short key, else None) and `said` (a refusal's words, else None).
- The sheet is `milestones.signoff`, a JSON object of section texts (`get_milestone_detail` reads it); a quoted line keeps its indent, as in `.softfield/reviews/f19-will-i-need-to-refresh-planning.md`.
- A `plant` request is a row of `owner_requests` (`kind = 'plant'`, `value` JSON with `text`, `ask`, `area` and, from the next ticket, `from`; `done`, `result` as "planted .softfield/cards/f166-plans-every-done-when-line-of.md" or the runner's refusal). `_review` in `factory_dashboard/planning.py` reads them the same way for a sign-off: follow it.
- The factory's own project (D2): the `projects` row whose `repo` folder holds `runner/loop.py` and `factory_dashboard/app.py`; `_repo` in `factory_dashboard/planning.py` reads a project's folder.
- `short_key` turns a card's file name into its short key.

### Done when
- a sheet whose `what_next` holds "- **Factory:**" then an indented "> Plans: …" line gives one factory idea with id "f19/1" and that text, without the ">"
- a quoted line under "- **Product:**" is a product idea planted in the review's own project; a factory idea from another project's review plants in the project whose folder holds the factory's code, and in its own when no project does
- no plant request: "plant"; one whose `from` is the id and `done` is NULL: "on its way"; done with "planted .softfield/cards/f166-….md": "planted" with card "f166"; done with any other result: "refused" with that result
- a hand-made plant whose text is the idea's without its final full stop counts as planted
- a sheet with no quoted line, or no sheet, gives no ideas
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2211
gate_failures: []
tokens: 3353988
```
