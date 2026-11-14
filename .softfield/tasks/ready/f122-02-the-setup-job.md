---
id: f122-02-the-setup-job
milestone: f122-new-project-from-the-projects-page
agent: lead
difficulty: 7
depends_on: [f122-01-new-project-request]
files:
  - runner/loop.py
  - runner/dispatch.py
  - runner/prompts.py
  - runner/planner.py
  - runner/requests.py
  - runner/instructions/bootstrap.md
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_prompts.py
  - tests/runner/test_requests.py
---

### Goal
The runner runs a queued `setup` job: the lead, headless, sets the new project up in its folder in one go from the owner's words, and its reply lands on M1's thread with ADR 00 as a proposal to approve.

### Context
Read D3 and D5 in `.softfield/cards/f122-new-project-from-the-projects-page.md` and ADR 48 items 4, 5 and 7. Then `run_planner` in `runner/loop.py` (the worked example: a Claude job whose JSON reply becomes a thread message), `PLANNER` in `runner/prompts.py`, the spec and allow-list code in `runner/claude.py`, `runner/instructions/bootstrap.md` and `runner/instructions/run-stack.md`.
- The job runs in the project's own folder on main, not a worktree or plan branch, on Opus, taking the claude lane in the planner's place in the order and under the reserve as planner jobs do. Its tools are ADR 48 item 4's, exactly; no `docker`, no `softfield accept` or `create`. It commits its own work.
- `prompts.SETUP` is bootstrap.md's text plus the form's values (name, idea, built with, app) and, on a later round, the owner's message or the failed findings. Write bootstrap.md's new section "From the Projects page": no chat; decide what the form doesn't say, with one line of why; follow every step of "A new project" and "Both" but the review in the chat; end with the JSON reply (points; one `adr` proposal for the project's ADR 00, .softfield/adr/00-initial.md, whose key points are the owner's ADR review format); ask in points only what it truly can't decide.
- bootstrap.md's "Both" gains a step for a project with pages, in both paths: its stack, as `runner/instructions/run-stack.md` says, the skeleton serving one page.
- A `plan_message` on a project paused `setting up` queues `setup`, not `planner`.
- A reply that isn't valid JSON is handled as `run_planner` handles one.

### Done when
- a queued `setup` job runs Claude in the project's folder with `prompts.SETUP` and the allow-list above, and its reply is stored on M1's thread with its points and its `adr` proposal
- the owner's message on a setting-up project's thread queues `setup`; on any other project it still queues `planner`
- the prompt carries the form's values and, when there are any, the owner's message
- bootstrap.md has the page's section and the stack step
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
