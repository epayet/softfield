---
id: f203-03-pushing-shows-on-the-bar
milestone: f203-push-to-github-at-sign-off
difficulty: 2
depends_on: []
agent: lead
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
While the runner pushes to GitHub, the top bar and the Overview say "pushing to GitHub", not "picking the next ticket", so a run that is busy pushing doesn't look stuck.

### Context
Read `check_push` and `doing` in `runner/loop.py`, and `test_a_pick_pushes_what_is_signed_off_and_doesnt_ask_again` in `tests/runner/test_loop.py`.
- On 2026-11-02 the first catch-up sent 64 tags, about 2 minutes, while the dashboard said "picking the next ticket", and the owner asked why the runner was doing nothing.
- Wrap the `push.push_signed_off` call in `with doing(s, "pushing to GitHub"):`. `doing` puts the activity back afterwards.
- A pick with no new tag doesn't contact the remote, so it must not show the words.

### Done when
- during `push.push_signed_off`, the run's activity is "pushing to GitHub", and afterwards it is what it was before
- a pick with no new tag never sets that activity
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 3
```
