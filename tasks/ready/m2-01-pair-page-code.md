---
id: m2-01-pair-page-code
milestone: 2
depends_on: []
files:
  - coucou/templates/coucou/pair.html
  - coucou/static/coucou/css/pair.css
  - coucou/locale/fr/LC_MESSAGES/django.po
  - coucou/locale/fr/LC_MESSAGES/django.mo
tests:
  - tests/integration/test_pair_page.py
max_diff: 80
---

### Goal
The pairing page gets its heading, the text of its "code" state and a small stylesheet, in English and French.

### Context
`coucou/templates/coucou/pair.html` is the page a new device shows at `/`. The script `coucou/static/coucou/js/pairing.js` fills `#pair-code` (e.g. `7K3M-Q9TD`) and `#pair-fingerprint` (e.g. `ABCD-EFGH-JKMN-PQRS`), and shows one `data-state` section at a time with the `hidden` attribute. **Keep every existing `id`, `data-*` and `hidden` attribute exactly as they are.**

The page loads `{% load i18n static %}` already. The server sends a Content-Security-Policy: no `style=` attributes, no `<style>` blocks, no inline `<script>`.

French: warm and simple, and always **vous** (never tu). French typography puts a space before `:` `!` `?`. `coucou/locale/fr/LC_MESSAGES/django.po` has only its header so far; add each entry as:

```
msgid "The code works for 10 minutes."
msgstr "Le code est valable 10 minutes."
```

### Pattern to follow
`coucou/templates/coucou/paired.html`

### Steps
1. In `<head>`, before the `<script>`, add `<link rel="stylesheet" href="{% static 'coucou/css/pair.css' %}">`.
2. As the first child of `<main id="pair">`, add `<h1>{% translate "Let's connect this device" %}</h1>`.
3. In `<section data-state="code" hidden>`, add three paragraphs with `{% translate %}`: before `#pair-code`, "To connect this device, give this code to the person who set up Coucou."; between `#pair-code` and `#pair-fingerprint`, `<p class="hint">` "They'll check that these letters match on their screen:"; after `#pair-fingerprint`, `<p class="hint">` "The code works for 10 minutes."
4. Create `coucou/static/coucou/css/pair.css` using system fonts only. It must contain `[hidden] { display: none !important; }`, a large bold `#pair-code`, and a monospace `#pair-fingerprint`. Centre `main` with a max width of about 36rem.
5. Add the French for the 4 new strings to `django.po`, then compile it with `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
