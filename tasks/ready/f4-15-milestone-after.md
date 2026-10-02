---
id: f4-15-milestone-after
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/loop.py
  - runner/tasks.py
  - runner/owner.py
  - docs/task-format.md
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_tasks.py
---

### Goal
A milestone doc may say `After: <key> signed off`, and its tickets aren't picked until the owner has signed that milestone off.

### Context
Read `docs/adr/17-always-on-factory.md` item 4, `runner/tasks.py` (`pick_next`, `blocked_ids`), `runner/loop.py` (`work_queue`, `_next_task`), `runner/owner.py` (`signoff`, how a milestone is marked done) and `runner/milestone.py` (`milestone_doc`). Test-first.
- The line sits in the milestone doc's header blockquote or under its title, e.g. `> **After:** f3-factory-line signed off`. Parse it in `runner/milestone.py`.
- "Signed off" means that milestone's doc says "Status: done" (what `signoff` writes). The `<key>-done` tag is a fallback.
- A ticket held this way is treated like one with undone dependencies: never picked. The verdict and `--dry-run` say "waits for f3-factory-line's sign-off". `runner run` goes on with other milestones.
- Document the line in `docs/task-format.md`'s "Milestone keys".

### Done when
- with `After: f3 signed off` and F3 not done, `pick_next` skips the milestone's tickets and `--dry-run` names the reason
- once F3's doc says done, they are picked
- a doc with no `After:` line changes nothing
- `uv run runner check-all --task f4-15-milestone-after` passes
