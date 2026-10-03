---
id: f4-05-opencode-shell-timeout
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 3
files:
  - runner/local_model.py
  - docs/agents/developer.md
tests:
  - tests/runner/test_local_model.py
---

### Goal
The runner sets OpenCode's default shell timeout, so a developer's `check-all` or test run isn't killed after 120 s.

### Context
Read `runner/local_model.py` (`run_opencode`), `runner/procs.py` (`run_streaming`, its `env`), and note 14 in `docs/agents/developer.md`. Test-first.
- **Fact (checked 2026-10-02):** OpenCode 1.18.32 (`/home/manu/.opencode/bin/opencode`) reads `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS`. Today nothing sets it, so a shell call is killed at 120 s with "(no output)". That cost nemotron-3-super f2-07 and earlier m4-03 and m4-06.
- Pass the runner's environment plus `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=900000` (15 min, under `[timeouts] gate`) to `run_streaming` for every OpenCode agent.
- Then rewrite note 14 of `docs/agents/developer.md` to keep only its second half ("(no output)" after a shell timeout means the call was killed…), since the timeout no longer needs passing by hand.

### Done when
- `run_opencode` starts OpenCode with that variable set to 900000, and the rest of the environment kept
- note 14 no longer asks developers to pass a timeout
- `uv run runner check-all --task f4-05-opencode-shell-timeout` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
