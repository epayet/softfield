---
id: f85-03-planner-lists-the-pages
milestone: f85-when-i-sign-off-a-task
agent: lead
difficulty: 2
depends_on: [f85-01-pictures-at-the-review]
files:
  - runner/prompts.py
  - runner/milestone.py
  - runner/instructions/lead.md
  - runner/instructions/bootstrap.md
tests:
  - tests/runner/test_prompts.py
---

### Goal
Every card the planner draws a mock-up for lists its pages under `## Before and after`, the review says in "What changed" whether the after pictures match the mock-up, and the setup session sets up `[shots]` for a new project with pages.

### Context
Read ADR 40 in `.softfield/adr/40-pictures-at-sign-off-in-every-project.md` (items 4, 6 and 7) and D1, D8, D9 and D10 in `.softfield/cards/f85-when-i-sign-off-a-task.md`, then the mock-up paragraph of `PLANNER` and the `REVIEW` brief in `runner/prompts.py`, the `prompts.REVIEW.format(...)` call in `review_milestone` (`runner/milestone.py`), "Planning room" in `runner/instructions/lead.md`, and `runner/instructions/bootstrap.md` (the setup session's guide). f85-01's script writes the pictures and their list file under the project's `.softfield/var/shots/` (D5).
- `PLANNER`, in the mock-up paragraph: when it draws a mock-up, the card doc gets a `## Before and after` section listing the addresses of the app's pages it changes, one backticked bullet each (on Softfield, a card's own page is `/milestones/<full key>`). In a project without `[shots]`, it still writes the list and says in a point that the project can't take pictures yet.
- `REVIEW` gets one more field: the after pictures' paths and the card's mock-up file, or "none" when there are no pictures. With pictures, it opens them with Read and ends "What changed" with one line: "Matches the mock-up" or what differs; a clear difference is a should-fix finding; an empty page because the sample data lacks something is said as such. With none, nothing changes.
- `lead.md`, Planning room: one line after the mock-up rule, so a terminal session lists the pages too.
- `runner/instructions/bootstrap.md`: for a project with pages, the setup fills in `[shots]` (`prepare` from the project's own fixtures, `serve`, `ready`), never on live data and with no call to a model or another service (ADR 40 item 4), and takes one picture to prove it before it ends.

### Done when
- `PLANNER` asks for the `## Before and after` section whenever it asks for a mock-up
- `REVIEW` formatted for a card with pictures names the after pictures and the mock-up; for a card without, it says none
- `lead.md` says the same in one line
- `runner/instructions/bootstrap.md` asks for `[shots]` on sample data for a project with pages
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
