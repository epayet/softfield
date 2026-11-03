---
id: bug-54-init-keeps-a-repos-own-hooks
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
finding: f127-shared-rules-stay-shared-across-projects-F7
files:
  - runner/setup.py
tests:
  - tests/runner/test_setup.py
---

### Goal
`softfield init` on a repo that already sets its own `core.hooksPath` (husky, for one) leaves it in place and says so, instead of switching the repo's hooks off without a word.

### Context
`setup.init` always runs `git config core.hooksPath .softfield/hooks`. ADR 41 item 1 says a person working without the factory sees a normal repo. A repo's own value is lost, and removing the factory doesn't bring it back. Leaving it costs little: the runner's gates still run on every ticket, and only the check at commit time is lost.

`init` returns `(origin, written)`, and `cli._machine_command` prints them. Hooks in `.git/hooks` with no `core.hooksPath` set are out of scope: the dot folder's README already says they don't run.

### Done when
- `init` on a repo whose `core.hooksPath` is set to another value leaves that value as it was, and its output tells the person that commits there skip `softfield check-all`
- `init` on a repo with no `core.hooksPath` sets it as today
- the listed `tests:` pass, and fail without the change
