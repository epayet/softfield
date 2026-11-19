---
id: f122-03-adr-00-adds-the-project
milestone: f122-new-project-from-the-projects-page
agent: lead
difficulty: 5
depends_on: [f122-02-the-setup-job]
files:
  - runner/requests.py
  - runner/setup.py
  - runner/loop.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_setup.py
---

### Goal
Approving ADR 00 of a project being set up from the page adds it to the factory when `softfield create`'s checks pass, and sends the setup back to the lead with what failed when they don't.

### Context
Read D4 in `.softfield/cards/f122-new-project-from-the-projects-page.md` and ADR 48 item 6. Then `_accept_adr` in `runner/requests.py`, `plan_first_card`, `doctor` and `passes` in `runner/setup.py`, and the `create` F236 added (its checks and its registration, D1 of `.softfield/cards/f236-softfield-init-adds-a-project-to.md`).
- Only on a project paused `setting up`; every other ADR approval is unchanged.
- Pass: the project is unpaused, its cards published, and "Plan this card." queued on M1 though its thread has begun (give `plan_first_card` a way to say so; the terminal path keeps today's refusal).
- Fail: a `setup` work item on M1's thread whose message lists the failing findings. Count the failures in a row; after the second, no job: an owner item on that project, "<name>'s setup stopped at: <findings>", cleared when a later approval passes.
- `create`'s checks run `check-all` in the project's folder; tests stub it.

### Done when
- approving a setting-up project's ADR 00 with passing checks leaves it unpaused, its cards on the board and one planner job waiting on M1
- with a failing check, a `setup` job waits with the findings in its message, and the project stays setting up
- a third failure in a row queues nothing and puts the "setup stopped" item on the desk
- approving an ADR on a live project does what it did before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
