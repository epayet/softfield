---
id: f236-01-doctor-registers-the-project
milestone: f236-softfield-init-adds-a-project-to
agent: lead
difficulty: 3
depends_on: [f136-03-start-fresh-wipes-the-old-entry]
files:
  - runner/setup.py
  - runner/cli.py
  - runner/owner.py
  - .softfield/adr/30-many-projects-one-factory.md
tests:
  - tests/runner/test_setup.py
  - tests/runner/test_owner.py
  - tests/runner/test_cli.py
---

### Goal
`softfield init` no longer puts the project in the factory's list: a new command, `softfield create`, does, once everything `softfield doctor` checks passes, and nothing else creates the project's row on the way. (The id predates the owner's choice of `create`: the registering is `create`'s, not `doctor`'s.)

### Context
Read D1 to D3 and D8 in `.softfield/cards/f236-softfield-init-adds-a-project-to.md`, then `init`, `register`, `ready`, `doctor`, `hand_over`, `publish_cards` and `plan_first_card` in `runner/setup.py`, the `init` branch of `_machine_command`, the `doctor` branch and the parser in `runner/cli.py`, `_write` and `decide_adr` in `runner/owner.py`, and `upsert_project`, `find_project`, `projects_in_order`, `FORGOTTEN` and `SETTING_UP` in `runner/metrics.py`.
- F136's tickets (f136-02, f136-03) changed `init` and `register` before this one: keep their question and its choices, and move only the registering of the new project (and the un-forgetting of "continue") to `create`. "Keep"'s rename of the old forgotten row stays at `init`.
- The name to register is `name` under `[project]` in the folder's `.softfield/project.toml`, not the folder's name.
- `create` is a project command (it runs in the project's folder, as `doctor` does). What `doctor`'s branch does after its checks pass today (`publish_cards`, `ready`, `plan_first_card`, `hand_over`) moves to `create`; `doctor` keeps its ADR 00 question.
- `init`'s printed line says "registered" today: it says `softfield create` adds the project when the setup is done.
- ADR 30 is Accepted: add a dated line under items 7 and 8 and under "A project is paused while it is set up", nothing else in it.

### Done when
- after `init` in a new folder, the metrics database holds no row for the project, and `projects_in_order` doesn't list it
- `softfield accept 0` in a folder whose project has no row commits the ADR and creates no row; on a registered project it resolves the owner items as today
- `softfield doctor` writes no row, passing or not; passing on an unregistered project, its last line names `softfield create`
- `softfield create` with every needed check passing registers the project last in the owner's order, not paused, with its cards published, the first card's planning asked for and the hand-over lines printed; with a needed check failing it writes no row and prints "Nothing was added to the factory."
- `create` on a folder whose `.softfield/project.toml` names a live project held by another folder fails with a message naming that folder and writes nothing; on an already registered project it says so and changes nothing
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
