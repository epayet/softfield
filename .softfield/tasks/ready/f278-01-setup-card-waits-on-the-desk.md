---
id: f278-01-setup-card-waits-on-the-desk
milestone: f278-until-the-setup-job-picks-up
agent: developer
difficulty: 1
files:
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
While a project's setup job is open, its first card shows on the desk as a reply on its way, never as a seed, and never drops off the desk.

### Context
Read D1 and "What happens today" in `.softfield/cards/f278-until-the-setup-job-picks-up.md`, then `_waiting_order`, `_answers_wanted` and `_seeds` in `factory_dashboard/planning.py`.
- `_waiting_order` already collects the threads of open `REPLIES` jobs (`planned`); add every card whose open job's kind is `SETUP` (import it from `runner.dispatch`, as `factory_dashboard/coming.py` does), whether or not the card has a thread or messages. Keep the order: these come after the threads already listed and before `_asked`'s, without repeats.
- `_seeds` leaves out any card `_waiting_order` lists.
- A setup job is queued with `metrics.queue_job(conn, project_id, "setup", "m1", reason, at)` and finished with `metrics.finish_queued`, as `tests/factory_dashboard/test_projects.py` does in `test_a_project_set_up_by_the_lead_lights_that_station_and_links_to_m1`.

### Done when
- an idea card `m1` with no thread and an open `setup` job on `m1` is not among the seeds, and is one item under "Your answers wanted", `on_its_way`, its words starting "waiting for the lead"
- the same with M1's thread made but holding no message: still that one item
- once the setup job is finished and the lead's message is the last, M1 is the usual "the lead replied …" item, not on its way; with the job finished and no thread, M1 is a seed again
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
