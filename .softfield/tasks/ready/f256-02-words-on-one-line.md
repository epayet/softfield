---
id: f256-02-words-on-one-line
milestone: f256-the-alignments-of-the-top-bar
agent: lead
difficulty: 1
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/_partials/bar_status.html
  - tests/factory_dashboard/test_app.py
  - .softfield/developer.md
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
Land the finished work of f256-02 from `blocked/f256-02-words-on-one-line` onto this ticket's branch, caught up with main, so that on a wide screen every word in the top bar's top row has the middle of its capitals on the row's centre line.

### Context
The work is done and passed `softfield check-all --task f256-02-words-on-one-line` on 2026-11-26. It was blocked only because the runner read the escalation's decision file from the old run's folder while the resumed session wrote it in the new one. A lead ticket starts from main, so the work comes across by hand:
- `git diff main...blocked/f256-02-words-on-one-line` is the whole change (5 files, about 116 lines); `git show blocked/f256-02-words-on-one-line:<path>` gives each file as it was finished. Apply it to these files with your edit tool, keeping whatever main has changed in them since.
- Read `.softfield/cards/f256-the-alignments-of-the-top-bar.md` ("Round 2", D6 to D8, and "As built"). Two facts the mock-up `.softfield/cards/f256-mockup/text-line.html` gets wrong, which the branch already handles, so keep them as they are: `text-box: trim-both` does nothing on a flex container, so each plate's words sit in their own trimmed `<span>` inside `.key` and `.val`; and the plate rules are scoped under `.bar-top`, because a bare `.tag` leaks onto the Ideas and Projects pages and the global `.key { margin: 8px 0 0 }` pushed the plate keys 4 px low.
- The branch also updated the `_job` and `_uptime` parsing helpers in `tests/factory_dashboard/test_app.py` and added two lines (notes 12 and 13) to `.softfield/developer.md`: bring both.

### Done when
- `git diff main` on this branch matches the blocked branch's change, adjusted only where main moved since
- at 1280 px, in both themes, with a developer job running, the branch's alignment test passes: the capital middles of the brand's name, the host, the status words, each plate's key and value and the project's name are within 1 px of the top row's centre
- clicking the Project plate opens the list, choosing a project reloads the page with it, and the plate shows a focus ring
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 4090447
logs: .softfield/var/runs/20261125-034732/f256-02-words-on-one-line
```

```yaml
# --- runner ---
result: blocked
reason: the escalation answered nothing on task/f256-02-words-on-one-line, not finish on task/f256-02-words-on-one-line; its work is on task/f256-02-words-on-one-line
```
