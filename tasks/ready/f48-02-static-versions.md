---
id: f48-02-static-versions
milestone: f48-the-didnt-go-through-cards-try
difficulty: 2
depends_on: []
files:
  - factory_dashboard/app.py
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/line.html
  - factory_dashboard/templates/overview.html
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
Every link to a file under `/static/` carries a version from the file's content, so a phone loads the new CSS or JS as soon as a merge changes it.

### Context
Read `factory_dashboard/app.py` (`templates` and its `templates.env.filters`, and the `/static` mount).
- F48 D4 (from F46): `base.html` loads `/static/dashboard.css` with no version, so a browser may keep the CSS from before a merge; after f31-06, the Dismiss button may have looked dead on the phone for that reason.
- D4: one Jinja global, `static(path)`, returns `/static/<path>?v=<the first 10 hex of the file's sha256>`. Cache the hash by path and the file's mtime: the server's `reload=True` restarts on a `.py` change only, so a merge that changes only the CSS must still give a new version.
- Use it for every `/static/` link in the templates: `base.html`, `thread.html`, `proposal.html`, `line.html`, `overview.html`, the vendor files included.
- A path that isn't a file under `factory_dashboard/static/` raises at render, so a typo fails a test.

### Done when
- every page's `<link>` and `<script>` to `/static/` carries `?v=` and the URL serves the file
- two files with different content get different versions; the same file the same version
- rewriting a file's content, with the server still running, changes its version
- no template has a bare `"/static/` link left (a test reads the templates)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
