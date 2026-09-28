---
id: m2-03-all-set-page
milestone: 2
depends_on: [m2-01-pair-page-code]
files:
  - coucou/templates/coucou/paired.html
  - coucou/locale/fr/LC_MESSAGES/django.po
  - coucou/locale/fr/LC_MESSAGES/django.mo
tests:
  - tests/integration/test_paired_page.py
max_diff: 60
---

### Goal
Once paired, a display and a phone each see a friendly "all set" page, in English or French.

### Context
`coucou/templates/coucou/paired.html` renders at `/display/` and `/phone/` for a paired device. Until the real apps exist it only needs a greeting. Its context has `kind` (`"display"` or `"phone"`) and `label` (the device's name from admin, e.g. "Mum's kitchen", possibly empty). The page's language is already chosen for the device. The current body is:

```html
  <main id="paired" data-kind="{{ kind }}"></main>
```

What the page must say (`tests/integration/test_paired_page.py` checks it):
- display: a `<h1>` "All set!", the label when there is one, and "Photos and notes will appear here."
- phone: a `<h1>` "You're connected!" and "Soon you'll be able to send moments from here."
- French for all four strings, in `coucou/locale/fr/LC_MESSAGES/django.po` (compiled to `django.mo` with `msgfmt`).

The Content-Security-Policy forbids `style=` attributes and inline scripts. The French is warm and simple, always **vous**, and **with all its accents** (é, è, à, ç…).

### Pattern to follow
`coucou/templates/coucou/pair.html`

### Steps
1. Make every test in `tests/integration/test_paired_page.py` pass, keeping `<main id="paired" data-kind="{{ kind }}">`. The strings must be translated with Django's `{% translate %}`, and the `.mo` file recompiled.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 131
gate_failures: []
```
