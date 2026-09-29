# Notes for juniors

Short on purpose: at most 15 notes (ADR 07). The lead keeps them current.

## Worked examples: copy their shape
- Pure rule + unit test: `coucou/ordering.py` → `tests/unit/test_ordering.py`
- Page + integration test: `coucou/templates/coucou/paired.html` → `tests/integration/test_me_page.py`
- JS UI module + browser test: `coucou/static/coucou/js/render.js` → `tests/browser/test_render.py`
- CSS + test: `coucou/static/coucou/css/display.css` → `tests/integration/test_display_css.py`
- Management command: `coucou/management/commands/post_moment.py` → `tests/integration/test_post_moment.py`

## Notes
1. French says `vous` and sounds warm and plain: "Réessayez un peu plus tard", never "Veuillez réessayer".
2. After editing a `.po` file, compile it with `msgfmt` (AGENTS.md rule 9).
3. Page text lives in the Django template, never in the JS. The JS shows or hides it.
4. Test the edges, not only the middle: empty, one, many, the longest note (280 characters), just before and after midnight.
5. A UI test checks the layout at phone and display sizes: `layout_problems(page) == []` (`tests/browser/conftest.py`).
6. Browser tests stub the network with `page.route`, never a real server.
7. A command that writes data refuses to run in production.
