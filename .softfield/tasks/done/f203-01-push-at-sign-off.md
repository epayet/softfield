---
id: f203-01-push-at-sign-off
milestone: f203-push-to-github-at-sign-off
difficulty: 5
depends_on: []
agent: lead
files:
  - runner/push.py
tests:
  - tests/runner/test_push.py
---

### Goal
ADR 42: the owner's sign-off pushes that commit and its tag, and nothing else, never forced, after a secret check.

---
**Done in the owner's terminal session of 2026-11-02.** Commit: "f-push-at-sign-off".
