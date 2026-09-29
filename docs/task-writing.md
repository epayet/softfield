# Writing tasks for the local model: what works

Practical guidance for whoever writes tickets: the lead, whichever frontier model that is ([`docs/agents/lead.md`](agents/lead.md)). The **rules** are in [`task-format.md`](task-format.md) and [ADR 01](adr/01-calibration-fixes.md); this page is the craft behind them, learned from calibration and M1 (see `docs/sessions/` and `docs/reviews/m1.md`).

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

## Since ADR 07: tickets, not solutions

Until M3 the lead wrote stubs, failing tests and a throwaway reference implementation for every task, then pasted the code into the spec. It worked (10/11 at the first attempt) but cost the lead more than doing the task. Now:

- **Goal:** one sentence.
- **Context:** the files to read (full paths) and the worked example to follow. Paste only facts no file holds: a decision from the milestone's Decisions section, an API the lead hasn't built yet. Put the one constraint that matters in **bold** (security, "admin-only: no gettext").
- **Done when:** acceptance criteria as bullets, including the edges ("a 280-character note", "just after midnight"). Whatever isn't written there, the junior won't test, and whatever isn't tested, it won't do.
- **No stubs, no reference implementation.** A spec error now shows up as a failed attempt or a `BLOCKED.md`, and a short escalation fixes it.
- **Security and protected work stay test-first:** the lead writes those tests on main, checks each fails for the right reason, and tests every security rule.
- **Where a data-writing command may run:** say so explicitly. The M1 review had to add a "never in prod" guard to `seed_demo`.

## JavaScript tasks (ADR 06)

- **Tests:** browser tests live in `tests/browser/test_<module>.py`, one file per module in `coucou/static/coucou/js/`. Each test imports the module on a blank harness page (`harness` fixture) and stubs the network with `page.route`. Example: `tests/browser/test_outbox.py`.
- **Which modules:** the local model gets UI modules (rendering, transitions, screen state). Crypto, auth, pairing, the outbox, the live stream, the service worker and `display.js` are protected.
- **Layout:** UI tests call `layout_problems(page)` at `PHONE` and `DISPLAY` sizes (`tests/browser/conftest.py`).
- **Strings:** Preact components (ADR 11) use `gettext()` in the JS, with the French in `djangojs.po`; list `djangojs.po` and `.mo` in `files:`. The display (plain modules until its port) keeps its text in the template.
- **Components:** point at `docs/agents/preact.md` and the worked example `name_form.js`; the ticket gives the props and the callbacks (the milestone's decisions), never the markup.

## Lessons from M2

- **The model can only produce what its tools allow.** For every file in `files:`, check that `opencode.json` lets the model create it. m2-01 listed `django.mo`, but `msgfmt` was denied: it cost one wasted attempt and an escalation (ADR 04).
- **French:** ask for "all its accents" explicitly (the model dropped them once), and give one tone example ("Réessayez un peu plus tard", not "Veuillez réessayer plus tard"). Claude still reads every `msgstr`.
- **Outcome-style specs** (what, not how) passed as reliably as dictation-style ones on small UI tasks: 2/2 against 1/1 at first attempt. ADR 07 builds on this.
- **Never wrap a runner session in an outer `timeout`.** It killed M2's runner mid-task. OpenCode's own limit is enough.
- **A test whose fixture someone fills in later must fail visibly,** never pass while empty (m2-F4). Juniors can't add skips (the `no-new-skips` gate).

## Before committing a spec

- `uv run ruff format --check .` and `uv run runner run --dry-run`, which prints each ticket's pre-flight problems. Before ADR 01, a mis-formatted code block in a spec failed ruff 3 times on a file the model couldn't touch.
- Don't edit the working tree while the runner runs. It does `git add -A`, so stray files join the task's diff.

## Lessons from M3

- **Estimated caps backfire.** m3-12's `max_diff` of 90 came from a one-line-per-rule CSS reference; the model writes one declaration per line and produced about 95. All 3 attempts went on trimming lines. Hence ADR 07's 1000-line backstop and no per-task caps.
- **Tests pin behaviour, not layout.** A screenshot pass found 4 layout problems no test caught. Hence the layout check.
- **Untested edges stay broken,** whoever writes the tests: m3-10's date bug was an edge missing from the lead's own skeleton tests.

## Open questions

- Outcome vs dictation: no visible difference in M2 (4 tasks). Keep sampling both.
- The model's French: correct grammar and `vous` when asked; stiff and word-by-word without tone examples. Does a tone example in Context close the gap?
