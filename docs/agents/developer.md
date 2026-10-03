# Notes for developers

Short on purpose: at most 15 notes (ADR 07). The lead keeps them current.

## Worked examples: copy their shape
- Pure rule + unit test: `coucou/ordering.py` → `tests/unit/test_ordering.py`
- Page + integration test: `coucou/templates/coucou/display.html` → `tests/integration/test_display_page.py`
- Preact component + browser test: `coucou/static/coucou/js/name_form.js` → `tests/browser/test_name_form.py` (read `docs/agents/preact.md` first)
- JS UI module + browser test: `coucou/static/coucou/js/render.js` → `tests/browser/test_render.py`
- CSS + test: `coucou/static/coucou/css/display.css` → `tests/integration/test_display_css.py`
- Management command: `coucou/management/commands/post_moment.py` → `tests/integration/test_post_moment.py`
- Dashboard page: `factory_dashboard/overview.py` (an `APIRouter` with its own SQL, included in `app.py`'s `create_app`) + `factory_dashboard/templates/overview.html` (extends `base.html`; a chart is a `data-chart` div, its JSON and a function in `static/charts.js`) → `tests/factory_dashboard/test_overview.py` (checks the rendered text and each chart's JSON)
- Factory line: the data and every rule in Python, `factory_dashboard/line.py` (`live_line`, a JSON block in the page; `line.py` imports from `overview.py`, so `overview.py` imports `live_line` inside `_live_context`, never at the top); the drawing only in `factory_dashboard/static/factory.js` (hand-written SVG) → `tests/factory_dashboard/test_line.py` (tests on the JSON, plus one browser test: the page from `TestClient`, `/static/` from disk with `page.route`)
- A live part's 5 s refresh in a browser: `open_overview` and the two tests after it in `tests/factory_dashboard/test_overview.py` (`/` and `/live` rendered on every request, the database changed between polls, waits longer than 5 s)
- A panel drawn from the line document, with numbers you choose: `with_clog` and the four tests after it in `tests/factory_dashboard/test_overview.py` (monkeypatch `factory_dashboard.line.live_line` to call the real one and then set one key; the rule lives in a small function in `overview.py`, not in `line.py`)

## Notes
1. French says `vous` and sounds warm and plain: "Réessayez un peu plus tard", never "Veuillez réessayer".
2. After editing a `.po` file, compile it with `msgfmt` (AGENTS.md rule 9).
3. Text lives where it's shown: `{% translate %}` in templates, `gettext("…")` with a literal in JS. JS French goes in `djangojs.po`, compiled to `djangojs.mo`.
4. Test the edges, not only the middle: empty, one, many, the longest note (280 characters), just before and after midnight.
5. A UI test checks the layout at phone and display sizes: `layout_problems(page) == []` (`tests/browser/conftest.py`).
6. Browser tests stub the network with `page.route`, never a real server.
7. A command that writes data refuses to run in production.
8. Lines stop at 100 characters. Your finish line (`check-all --fix`) formats for you: it joins lines that fit, but won't split a long string (JS inside a Python test). Split only a string that's still too long.
9. Check `workflow/protected-paths.txt` before your first edit. If the task needs a protected file changed, don't try: write `BLOCKED.md` with `CATEGORY: needs-file` straight away.
10. Before writing an expected list from test data, follow the fixture chain down to its root (`db_path` seeds rows too), and remember `runner.metrics` upserts: writing a row with an existing key updates it rather than adding one. If the count the test sees differs from yours, trust the page and recount; don't adjust the regex until it matches.
11. If `all-tests` fails in a test about another ticket or a file outside your `files:` (f1-35: `test_tasks.py` naming f1-36), main was red before you. Don't try to fix it: finish your own work and write `BLOCKED.md`: a first line that is exactly `CATEGORY: needs-file`, the failing test's name on the next line.
12. When a number in your ticket disagrees with your count, write the rows out as a table (duration in seconds, each token column) and add them once; never change fixture rows or invent new ones to make a number fit.
13. A ticket that replaces a behaviour replaces its tests: rewrite the tests in your `tests:` that pin the old one, and never leave an assertion that can't fail. Keep them as narrow: an assertion within a panel that goes moves to the panel that replaces it, never to the whole page (f3-05).
14. `check-all` and the full test suite take several minutes: give their shell call a timeout of 900000 ms. "(no output)" after a shell timeout means the call was killed, not that the checks hang; never write `BLOCKED.md` for it.
15. To add to an existing file, Edit it, anchored on its last lines; never Write it: Write replaces the whole file (f2-07 wiped the 1,300-line dashboard `conftest.py` and lost the attempt). You can't delete or rename files, so create only those your ticket names: f3-16 made two empty ones and spent its last attempt failing to remove them.
