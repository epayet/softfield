---
id: f38-02-updated-note
milestone: f38-the-refresh-prompt-causes-layout-shifting
agent: lead
difficulty: 2
depends_on: [f38-03-fake-clock-ignores-subprocess]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
A page that loaded the new version by itself says so for 15 seconds: "✓ Updated HH:MM" where the "↻ New version" tag hangs, so the owner can tell the page is current.

### Context
**The work is already finished: bring it over, don't build it again.** It's on the git branch blocked/f38-02-updated-note, which the runner keeps when this ticket comes back. Your own branch starts from main, so read the finished work with `git diff main...blocked/f38-02-updated-note` and make the same changes with Edit, in the four files it changes: the two in `files:`, `tests/factory_dashboard/test_app.py` and the note it adds to `.softfield/developer.md`. Where main has moved in those files, keep main's changes as well. Don't redesign anything, and don't rewrite its tests: they drive the real reloads on the page's clock.

It failed `check-all` only on a test outside this work (see D5 in `.softfield/cards/f38-the-refresh-prompt-causes-layout-shifting.md`), mended by f38-03-fake-clock-ignores-subprocess. If a test outside these files fails again, say which and why in your notes; don't change it here.

The picture it builds: `.softfield/cards/f38-mockup/updated-note.html` (Proposed).

### Done when
- `git diff main...blocked/f38-02-updated-note` and your branch's diff from main make the same changes, apart from where main has moved
- in a browser test, a page that reloads through the hidden-page path shows "Updated" and a time in `.bar-stripe`, and it's gone after 15 s (on the page's clock)
- a page loaded by hand (no stored key) shows no "Updated" note
- the header's height and the top of `<main>` don't change when the note appears or goes
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 9261133
logs: .softfield/var/runs/20261103-163949/f38-02-updated-note
```

```yaml
# --- runner ---
result: blocked
reason: the finished work failed check-all; its work is on task/f38-02-updated-note
```
