---
id: f268-02-pictures-reach-the-card-and-the-lead
milestone: f268-having-the-ability-to-upload-files
agent: lead
difficulty: 5
depends_on: [f268-01-pictures-stored-with-the-request]
area: factory
files:
  - runner/requests.py
  - runner/planner.py
  - runner/prompts.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_planner.py
---

### Goal
At its pick the runner moves a plant's or a message's files out of the database into `.softfield/var/files/` and the backup folder, unchanged, and the planner job is told to open them.

### Context
Read ADR 49 items 3 and 5, and D1, D5, D6 in `.softfield/cards/f268-having-the-ability-to-upload-files.md`. A plant is applied by `_plant` in `runner/requests.py` (it writes the card doc and commits it with `_commit_files`); a message by `_plan_message`. The backup folder is `Backup.dir` in `runner/config.py`. `message` in `runner/planner.py` reads a message's value, and `prompt` there builds the planner job's prompt; the planner's brief is `PLANNER` in `runner/prompts.py`. The files' bytes are in `owner_files` (f268-01), by the ids in the value's `files`. `runner/` is protected: tests first.

### Done when
- applying a `plant` with two files writes each to `.softfield/var/files/<card>/<request id>-<n>-<name>` and to `<backup dir>/files/<project>/` with the same name, both byte for byte equal to what was sent; the row's `path` is set and its `bytes` emptied; nothing under `.softfield/var/files/` is committed
- the planted card's Notes, in the commit that makes the doc, have `Files (for the lead, not in git):` and one bullet per file with its name, size and path
- applying a `plan_message` with a file does the same under the card's folder, or `general/` on the general thread, and commits nothing
- with no backup folder set, the file is still written to `.softfield/var/files/` and the run log says the backup copy was skipped
- the planner job's prompt for a message with files names each path, type and size, and says to open each with Read before answering and to say in a point if one can't be opened; one without files is unchanged
- `PLANNER` says in one line that a file is part of the owner's note
- a plant or message without `files` is applied exactly as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
