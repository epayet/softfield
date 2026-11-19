---
id: f274-01-refuse-a-prefix-that-cant-match
milestone: f274-pre-flight-refuses-a-command-prefix
difficulty: 2
depends_on: []
files:
  - runner/tasks.py
  - runner/instructions/task-format.md
  - .softfield/tasks/ready/f231-01-clear-the-seed-row.md
tests:
  - tests/runner/test_tasks.py
agent: lead
area: factory
---

### Goal
Pre-flight refuses a lead ticket's `commands:` entry that ends in an address or a cut-off word, since Claude Code matches a prefix only at a word boundary and such an entry allows only itself.

### Context
Read D1 to D4 of `.softfield/cards/f274-pre-flight-refuses-a-command-prefix.md`.
- `_commands` in `runner/tasks.py` is where entries are checked; `test_commands_never_reach_git_or_the_owners_commands` in `tests/runner/test_tasks.py` is the example for the new tests.
- `runner/claude.py` turns each entry into `Bash(<entry>:*)`.
- The case that cost a blocked ticket: `curl -s https://danbooru.donmai.us/`, whose job then had every `curl -s https://danbooru.donmai.us/tags.json?…` refused.

### Done when
- an entry whose last word holds `://`, or ends in `/`, `=` or `?`, is refused with a `TaskError` naming the entry and saying, in D2's words, that it matches only itself and to end the entry before it
- an entry with a `?` gets that message, not the generic "may not include"
- `ollama list`, `gh api`, `rm docs/old.md` and `softfield run --dry-run` still pass; `git` and the owner's commands are still refused as before
- `runner/instructions/task-format.md` says so in one line beside `commands:`
- if `.softfield/tasks/ready/f231-01-clear-the-seed-row.md` is still there, its `rm .softfield/tasks/later/` entry (which the new rule refuses, and which could never match `rm .softfield/tasks/later/bug-05-….md`) becomes `rm`, and nothing else in it changes (D5)
- every ready ticket still passes `softfield check-tickets`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
