# Milestone F121: Projects on any main branch, in any language

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

Make `softfield init` and the gates work on any repo.

**Main branch.** The factory assumes a branch called `main` everywhere (`MAIN` in runner/loop.py,
runner/planner.py, `setup.init`). Setting up a copy of fact-printer (which is on `master`) was
refused; `init` now says to rename the branch. Proposed: `[project] main = "master"` in
`.softfield/project.toml`, read wherever `MAIN` is used.

**Check commands.** check-all and the gates still run Python's tools, whatever the project:
- lint: `uv run ruff check .` and `ruff format --check .` (runner/checks.py, `gate_ruff`);
- auto-format before the gates: ruff on changed `.py` files (`gates.autoformat`);
- a ticket's tests and the suite: `uv run pytest` (`gate_task_tests`, `gate_all_tests`);
- "new tests fail without the change": pytest's exit codes 1/2 and 5 (`gate_tests_fail_on_main`);
- no new skips: pytest's skip/xfail patterns (`gate_no_new_skips`);
- one test file per module: `test_x.py` ↔ `x.py` (`layout_problems`);
- what the local developer may run: `agents.CHECK_COMMANDS` and `opencode.json`.
Already stack-free: protected paths, diff size, dependency files, BLOCKED.md, planning, reviews.

Proposed `[checks]` keys, Python with uv staying the default so Coucou and Softfield don't change:
```toml
lint = ["npm", "run", "lint"]
format = ["npx", "prettier", "--write"]   # on the changed files before the gates
test = ["npx", "vitest", "run"]           # a ticket's tests appended; the suite gets test_dirs
skip_patterns = ['\.skip\(', '\.only\(']
```
"Tests fail on main" becomes: any non-zero exit means they failed. Proof: one small JavaScript
project set up with `softfield init`. About one session of protected runner code.

## Plan (lead, 2026-10-27)

**Expected outcome.** A project on `master`, or not in Python, can be set up with `softfield init`
and run by the factory: its main branch, its lint, its fixes, its tests and "your tests fail
without your change" come from its `.softfield/project.toml`. Softfield, Coucou and
travel-companion change nothing: every default is today's command, word for word.

**Done when.** A test project on `master` whose checks are plain shell commands passes
`check-all` and every gate, and fails them where it should (f121-05); and at sign-off a small
JavaScript repo is set up with `softfield init` and `softfield doctor` passes on it.

**Why no ADR.** ADR 30 already decided it: item 1 puts "main branch, check commands" in
`project.toml`, item 3 says "the runner's checks and gates run the project's commands". This card
finishes what ADR 30 left hard-coded; the gates keep their rules (ADR 07 item 4 included).

**Checked on 2026-10-27:** all three projects are Python with uv, on `main`. Nothing needs this
card today; fact-printer, the one that did, was a trial copy.

### Decisions
- **D1. The main branch.** `main` under `[project]`, `"main"` when missing;
  `config.project_main(repo) -> str` reads it. Every use of `loop.MAIN`, `planner._MAIN` and the
  literal `"main"` in `runner/` (loop, planner, requests, milestone, bench, setup, prompts) takes
  the project's, read once per project session (the session carries it; no module constant).
  `softfield init` on an existing repo no longer refuses another branch: it writes
  `main = "<the branch it is on>"`. A fresh `git init` still makes `main`. `doctor` says "on
  <main>".
- **D2. Commands are argv lists, never a shell string.** `lint` is a list of commands, each must
  exit 0; `fix` a list of commands the runner ends with the files (before the gates) or `.`
  (`check-all --fix`); `test` one command the runner ends with a ticket's tests or the suite.
  Defaults: `lint = [["uv","run","ruff","check","."], ["uv","run","ruff","format","--check","."]]`,
  `fix = [["uv","run","ruff","check","--fix","--force-exclude"], ["uv","run","ruff","format","--force-exclude"]]`,
  `test = ["uv","run","pytest","-q","-p","no:cacheprovider"]`, `fix_suffixes = [".py"]`.
  `mypy` stays as it is (Python's type check); another stack puts its type check in `lint`.
  `test_workers` stays pytest's: `-n` is added only when it is above 0.
- **D3. One name, "lint".** check-all's "ruff check" and "ruff format" become one check, `lint`;
  the gate `ruff` becomes `lint`, in `MECHANICAL` and `HINTS` too. Its hint names the project's
  own fix commands. Old metrics rows keep "ruff": history, no migration.
- **D4. What counts as a test.** `test_files`, globs, default `["tests/**/test_*.py"]`, with
  `tests/e2e/` still left out; `fails_on_main`, exit codes, default `[1, 2]` (pytest: failed, or
  couldn't import); `skip_patterns`, regexes, default today's `_SKIP_RE`. `is_test_file`, the
  `no-new-skips` diff and the tests-only rule read them instead of `tests/` and `.py`.
  A JavaScript project sets `fails_on_main = [1]`, not "any non-zero": a config error or a
  missing file must not pass as "your tests fail".
- **D5. Left Python-only, on purpose:** `[checks.layouts]` (a project with none has no layout
  rule), the weak-pattern gate (only in `tests/browser/` and `tests/e2e/`), the end-to-end run
  (only with `e2e` set, F135 D1) and the translations check. Each becomes a key when a project
  needs it, not before.
- **D6. What Claude's jobs may run.** `CHECK_COMMANDS` becomes the project's: its lint, fix, test
  and mypy commands as Bash prefixes, plus `softfield check-all`. The prompts' `uv run pytest -q
  {tests}` reads the project's `test`. The local developer's `opencode.json` already allows only
  `softfield check-all`: unchanged.

- **D7. One guide per language** (owner, 2026-10-27: "would language preferences be better
  managed in their own files? python.md"). Each guide is `docs/agents/stacks/<name>.md` in Softfield,
  shaped like `docs/agents/preact.md`: how to write and test code in that language, then the
  `[checks]` lines a project in it starts from, which the setup session copies. A project names its
  guides in `[project] stacks` (`["python"]` when missing). The commands themselves stay in
  `project.toml`, the one place the runner reads, so a project can still differ (jest or vitest).
  Each project's `.softfield/project.md` keeps only what is its own (the product, its taste).
  `javascript.md` is written when the first JavaScript project is set up, from that project.

**Board place (owner, 2026-10-27):** at the back of the queue; a JavaScript project is coming,
and its setup is the real proof at sign-off.

### Tickets (all the lead's: `runner/` is protected)
| Ticket | What | Waits for |
|---|---|---|
| f121-01-main-branch-per-project | D1 | — |
| f121-02-check-commands-from-project | D2, D3 | — |
| f121-03-what-counts-as-a-test | D4 | 02 |
| f121-04-jobs-run-the-projects-checks | D6 | 02 |
| f121-05-a-project-on-master-not-python | the proof, the template, `doctor` | 01, 03, 04 |
| f121-06-a-guide-per-language | D7: `python.md`, `[project] stacks` | 03, 04 |
