---
id: m2-02-pair-page-states
milestone: 2
depends_on: [m2-01-pair-page-code]
files:
  - coucou/templates/coucou/pair.html
  - coucou/locale/fr/LC_MESSAGES/django.po
  - coucou/locale/fr/LC_MESSAGES/django.mo
tests:
  - tests/integration/test_pair_page_states.py
max_diff: 80
---

### Goal
The pairing page's other states and error messages get their text, in English and French.

### Context
In `coucou/templates/coucou/pair.html`, these elements are still empty:

```html
    <section data-state="starting"></section>
    <section data-state="expired" hidden>
      <button id="pair-renew" type="button"></button>
    </section>
    <section data-state="unsupported" hidden></section>
    <section data-state="error" hidden>
      <p data-error="rate_limited" hidden></p>
      <p data-error="too_many_pending" hidden></p>
      <p data-error="network" hidden></p>
      <p data-error="generic" hidden></p>
      <button id="pair-retry" type="button"></button>
    </section>
```

The script `coucou/static/coucou/js/pairing.js` shows and hides them. **Keep every existing `id`, `data-*` and `hidden` attribute exactly as they are.** No `style=` attributes and no inline `<script>`: the Content-Security-Policy forbids them.

French: warm and simple, always **vous** (never tu), and **with all its accents** (é, è, à, ç…). French typography puts a space before `:` `!` `?`. Add entries to `coucou/locale/fr/LC_MESSAGES/django.po` after the existing ones, as `msgid "..."` / `msgstr "..."` pairs.

### Pattern to follow
`coucou/templates/coucou/paired.html`

### Steps
1. Wrap every text in `{% translate "..." %}`, exactly as given here (the tests compare it).
2. `starting`: `<p>` "Getting ready…" (with the single character `…`). `expired`: before the button, `<p>` "This code has expired."; the `#pair-renew` button text is "Get a new code". `unsupported`: `<p>` "This browser can't connect to Coucou. Try an up-to-date Chrome or Safari."
3. Error messages go inside the existing `<p data-error=...>` elements: `rate_limited` "Too many tries for now. Please wait a few minutes and try again."; `too_many_pending` "Lots of devices are waiting to be connected. Please try again later."; `network` "Can't reach Coucou right now. It will keep trying."; `generic` "Something went wrong."; the `#pair-retry` button text is "Try again".
4. Add the French for all 10 new strings to `django.po`, then compile it with `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 129
gate_failures: []
tokens: 64930  # backfilled from docs/sessions/
```
