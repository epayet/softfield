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
- **Done when:** acceptance criteria as bullets, including the edges ("a 280-character note", "just after midnight"). Whatever isn't written there, the developer won't test, and whatever isn't tested, it won't do.
- **No stubs, no reference implementation.** A spec error now shows up as a failed attempt or a `BLOCKED.md`, and a short escalation fixes it.
- **Security and protected work stay test-first:** the lead writes those tests on main, checks each fails for the right reason, and tests every security rule.
- **`tests:` names a file the developer may write.** If the natural test file is protected (`tests/browser/test_display.py` guards `display.js`), the lead writes those tests on main first, and the developer's ticket points at them. Never ask for a new test file with no module of its own: the layout gate wants a matching module, and m4-07's junior invented an empty one to satisfy it (m4-F7). Listing the protected file burned three attempts.
- **Where a data-writing command may run:** say so explicitly. The M1 review had to add a "never in prod" guard to `seed_demo`.

## Difficulty (ADR 14 item 5)

Every ticket gets `difficulty:` from 1 to 10 when it's written. Ratings and routing play each ticket against it, so estimate the ticket as written, not the developer you expect. Start at 1 and add:

| Factor | +0 | +1 | +2 |
|---|---|---|---|
| Concepts | one | two or three | four or more, interlocked |
| Files to read (beyond those it changes) | 0–2 | 3–5 | 6 or more |
| Files to change (a `.po` and its `.mo` count as one) | one | two or more | |
| Dependencies on fresh code (another ticket's work) | none | one or two | three or more |
| A new pattern (no worked example to follow) | | yes | |
| UI (a screen, browser tests, the layout check) | | yes | |
| i18n (new strings with their French) | | yes | |
| Offline, storage or timing (events, races, held requests) | | yes | |

Steps that dictate the code take a point or two off. Then round by judgement against these anchors from M1–M4:

| d | Ticket | Why |
|---|---|---|
| 1 | m1-03-vault-list-counts | two counts on an admin list, dictated |
| 3 | m3-03-build-snapshot | a pure function on top of `current_content` |
| 5 | m3-10-render-names-nav | four DOM helpers and the date edges of `Intl` |
| 7 | m4-08-sent-log | a new storage module wired into `/me/`, quota errors, i18n |
| 9 | m4-06-me-wiring | four components wired through the outbox, i18n and offline; failed until split |
| 10 | | only the lead should do this: security, protected paths, a design call |

A sum of 9 or more on a developer ticket means split it, or make it a lead ticket (as m4-06 shows). At review, when the estimate was clearly off, the lead sets `difficulty_corrected:` beside it and leaves `difficulty:` as it was.

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
- **A test whose fixture someone fills in later must fail visibly,** never pass while empty (m2-F4). Developers can't add skips (the `no-new-skips` gate).

## Before committing a spec

- `uv run ruff format --check .` and `uv run runner run --dry-run`, which prints each ticket's pre-flight problems. Before ADR 01, a mis-formatted code block in a spec failed ruff 3 times on a file the model couldn't touch.
- Pre-flight resolves every backticked name ending in `.py`, `.js`, `.html`, `.css`, `.md`, `.toml`, `.json` or `.txt` in Context from the repo root. Write such names as full paths (`coucou/static/coucou/js/delivery.js`, not a bare `delivery.js`), and put import specifiers like "./outbox.js" in quotes. m4-06 lost two runs to this. Headless escalations can't run `--dry-run`, so grep your Context for backticked bare filenames before requeueing.
- Don't edit the working tree while the runner runs. It does `git add -A`, so stray files join the task's diff.

## Lessons from M3

- **Estimated caps backfire.** m3-12's `max_diff` of 90 came from a one-line-per-rule CSS reference; the model writes one declaration per line and produced about 95. All 3 attempts went on trimming lines. Hence ADR 07's 1000-line backstop and no per-task caps.
- **Tests pin behaviour, not layout.** A screenshot pass found 4 layout problems no test caught. Hence the layout check.
- **Untested edges stay broken,** whoever writes the tests: m3-10's date bug was an edge missing from the lead's own skeleton tests.

## Lessons from M4

- **Nothing CSS can't do.** m4-07 asked plain CSS to tell long notes from short ones; it can't, so the developer shrank every note (m4-F6). If the rule needs data (a length, a count), say which module marks it (a class, an attribute).
- **"Done when" says what the screen shows,** not only that something appears: "the item shows its note and thumbnail", not "an item appears". Developers' tests check exactly what the ticket names (m4-F2).
- **Ask for tests that act as a person would:** click, fill, `select_option`. A test that dispatches events or sets `.value` from JavaScript reaches states nobody can (m4-F1). The `test-patterns` gate flags it (ADR 12).
- **Split wide fan-in.** A developer ticket depends on at most two other developer tickets. m4-06 wired four, plus i18n and offline, and failed until it was split. Past two, split it or make it a lead ticket (ADR 12).

## Open questions

- Outcome vs dictation: no visible difference in M2 (4 tasks). Keep sampling both.
- The model's French: correct grammar and `vous` when asked; stiff and word-by-word without tone examples. Does a tone example in Context close the gap?
