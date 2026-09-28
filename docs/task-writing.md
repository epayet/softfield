# Writing tasks for the local model: what works

Practical guidance for whoever writes tasks (today Claude, but any frontier model or a person). The **rules** are in [`task-format.md`](task-format.md) and [ADR 01](adr/01-calibration-fixes.md); this page is the craft behind them, learned from calibration and M1 (see `docs/sessions/` and `docs/reviews/m1.md`).

**Evidence so far:** 5 tasks. 3/3 passed on the first attempt once these practices were in place. The 2 failures before that were both spec errors, not model errors.

## The local model (Qwen 3.6 35B-A3B via OpenCode)

**Good at:**
- following precise Steps literally and correctly;
- not exploring: it reads only the files it's pointed at;
- fixing lint it sees in tool output.

**Weak at:**
- **Long prompts:** instructions in the middle get dropped. In calibration it never ran mypy, although the Steps asked.
- **Retries:** it can ignore the gate output and declare success, especially when the failure is in a file it can't touch.
- **Unstated cases:** told to report "if anything was created", it tracked only the objects it had assigned to variables. Whatever the tests don't pin, it doesn't do.

## Before the task: the skeleton

1. **Stubs** with the final signature and docstring, and `raise NotImplementedError` as the body. The model fills in a shape; it doesn't design one.
2. **Failing tests, one test file per task.** The task-tests gate runs whole files, so a file shared with another queued task fails on that task's skeleton tests.
3. **Check each test fails for the right reason.** Tighten any that pass early. For example, the word "Vaults" was already in the admin's side navigation, so the test now checks for `column-vaults`.
4. **Write a throwaway reference implementation.** Run the tests, ruff and mypy against it, then revert it. This catches impossible tests: M1's query-count limit was wrong (a prefetch takes 3 queries, not 2). It also gives the real diff size for `max_diff`.
5. **Test every security rule.** For example, assert that the secret fields never appear in the admin inline.

## The spec itself

- **Goal:** one sentence.
- **Context:** paste the current code the model will edit, verbatim, plus only the facts it would otherwise look up (a `related_name`, a choices label). Leave out background and anything "for completeness". Put the one constraint that matters in **bold** (security, "admin-only: no gettext").
- **Steps:** close to dictation. Give the exact imports, the exact expression to return, and the trap to avoid ("use `.all()`, not `.filter()`, so the prefetch is used"; "the `getattr` keeps mypy happy").
- **Where a data-writing command may run:** say so explicitly. The M1 review had to add a "never in prod" guard to `seed_demo`.
- **Size:** about 10–60 changed lines. Grow it only if first-attempt pass rates stay high.

## Lessons from M2

- **The model can only produce what its tools allow.** For every file in `files:`, check that `opencode.json` lets the model create it. m2-01 listed `django.mo`, but `msgfmt` was denied: it cost one wasted attempt and an escalation (ADR 04).
- **French:** ask for "all its accents" explicitly (the model dropped them once), and give one tone example ("Réessayez un peu plus tard", not "Veuillez réessayer plus tard"). Claude still reads every `msgstr`.
- **Outcome-style specs** (what, not how) passed as reliably as dictation-style ones on small UI tasks: 2/2 against 1/1 at first attempt. Both work when Context pastes the skeleton.
- **Never wrap a runner session in an outer `timeout`.** It killed M2's runner mid-task. OpenCode's own limit is enough.
- **A test whose fixture someone fills in later must skip visibly,** never pass while empty (m2-F4).

## Before committing a spec

- `uv run ruff format --check .` and `uv run runner run --dry-run`, which includes pre-flight. Before ADR 01, a mis-formatted code block in a spec failed ruff 3 times on a file the model couldn't touch.
- Don't edit the working tree while the runner runs. It does `git add -A`, so stray files join the task's diff.

## Open questions

- Outcome vs dictation: no visible difference in M2 (4 tasks). Keep sampling both.
- The model's French: correct grammar and `vous` when asked; stiff and word-by-word without tone examples. Does a tone example in Context close the gap?
