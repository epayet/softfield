---
id: f122-01-new-project-request
milestone: f122-new-project-from-the-projects-page
agent: lead
difficulty: 5
depends_on: [f236-02-setup-ends-at-the-session-exit]
files:
  - runner/config.py
  - runner/requests.py
  - runner/setup.py
  - factory_dashboard/requests.py
tests:
  - tests/runner/test_config.py
  - tests/runner/test_requests.py
  - tests/runner/test_setup.py
  - tests/factory_dashboard/test_requests.py
---

### Goal
A `new_project` request from the dashboard makes the project's folder under the machine's projects root, keeps the owner's idea word for word, writes its first card and registers it "setting up", with a `setup` job queued on M1's thread.

### Context
Read D1 and D2 in `.softfield/cards/f122-new-project-from-the-projects-page.md` and ADR 48 items 1 to 3 (`.softfield/adr/48-start-a-project-from-the-projects-page.md`). Then `machine_file`, `machine_ntfy` and `project_name` in `runner/config.py`; `init`, `register` and `publish_cards` in `runner/setup.py` (as F236 and F136 left them: `init` writes no row, and takes F136's answer for a forgotten name); `_project_order` and the kinds list in `runner/requests.py`; `KINDS` in `factory_dashboard/requests.py`.
- `config.projects_root() -> Path` as D1 says; the common parent is taken over live rows only (`paused` not `forgotten`).
- The request rides on Softfield's own project row, like `project_order`. Its handler returns a plain result line naming the folder and the thread ("set up in ~/projects/epayet/bird-log; its setup comes on M1's thread").
- Never refuse the owner's words for their form (owner.md, "never refused unseen"): a name is slugged, a taken one takes `-2`; only an empty idea is refused, with words the request's status shows.
- The `setup` work kind is only queued here (a constant beside `dispatch.PLANNER` in `runner/dispatch.py`); f122-02 runs it. Until then the picker must leave it alone, not crash on it.
- Tests use a temporary root and database: nothing under the real home.

### Done when
- `[projects] root` is read and `~`-expanded; without it, the common parent of the live projects' folders, else `~/projects`
- a `new_project` request makes `<root>/<slug>` with the factory's files, `.softfield/seed.md` holding the idea byte for byte under `# Seed` and the date, and `.softfield/cards/m1-first-version.md` as D2 says, in one commit on main
- the project is registered paused `setting up`, its card is on its board, and one `setup` work item waits on thread `m1`
- a taken folder or a live name gets `-2`; an empty name takes a slug of the idea's first words; an empty idea is refused and nothing is written
- the dashboard's `/requests` accepts the kind
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
