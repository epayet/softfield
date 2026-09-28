---
id: m3-06-bad-origin-message
milestone: 3
depends_on: []
files:
  - coucou/templates/coucou/pair.html
  - coucou/locale/fr/LC_MESSAGES/django.po
  - coucou/locale/fr/LC_MESSAGES/django.mo
tests:
  - tests/integration/test_pair_page_bad_origin.py
max_diff: 20
---

### Goal
When Coucou is opened at the wrong address, the pairing page says which address to use instead of "Something went wrong."

### Context
In `coucou/templates/coucou/pair.html`, the error section has one `<p data-error="…" hidden>` per error code, for example:

```html
      <p data-error="generic" hidden>{% translate "Something went wrong." %}</p>
```

The page's JavaScript already shows the `<p>` whose `data-error` matches the server's error code. The view passes the address as `public_origin`.

### Pattern to follow
The other `data-error` lines in `coucou/templates/coucou/pair.html`.

### Steps
1. Add this line just above the `generic` one, exactly as written:
   `<p data-error="bad_origin" hidden>{% translate "Open Coucou at its usual address:" %} <a href="{{ public_origin }}">{{ public_origin }}</a></p>`
2. In `coucou/locale/fr/LC_MESSAGES/django.po`, translate `"Open Coucou at its usual address:"` as `"Ouvrez Coucou à son adresse habituelle :"`, keeping all its accents and the space before the colon.
3. Compile the catalogue: `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po`. **Copy the English and French strings exactly: the tests compare them character for character.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 87
gate_failures: []
tokens: 71869
```
