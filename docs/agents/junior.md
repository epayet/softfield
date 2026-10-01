# Notes for juniors

Short on purpose: at most 15 notes (ADR 07). The lead keeps them current.

## Worked examples: copy their shape
- Pure rule + unit test: `coucou/ordering.py` → `tests/unit/test_ordering.py`
- Page + integration test: `coucou/templates/coucou/display.html` → `tests/integration/test_display_page.py`
- Preact component + browser test: `coucou/static/coucou/js/name_form.js` → `tests/browser/test_name_form.py` (read `docs/agents/preact.md` first)
- JS UI module + browser test: `coucou/static/coucou/js/render.js` → `tests/browser/test_render.py`
- CSS + test: `coucou/static/coucou/css/display.css` → `tests/integration/test_display_css.py`
- Management command: `coucou/management/commands/post_moment.py` → `tests/integration/test_post_moment.py`
- Dashboard page: `factory_dashboard/overview.py` (an `APIRouter` with its own SQL, included in `app.py`'s `create_app`) + `factory_dashboard/templates/overview.html` (extends `base.html`; a chart is a `data-chart` div, its JSON and a function in `static/charts.js`) → `tests/factory_dashboard/test_overview.py` (checks the rendered text and each chart's JSON)

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
11. If `all-tests` fails in a test about another ticket or a file outside your `files:` (f1-35: `test_tasks.py` naming f1-36), main was red before you. Don't try to fix it: finish your own work and write `BLOCKED.md` with `CATEGORY: needs-file` and the failing test's name.
