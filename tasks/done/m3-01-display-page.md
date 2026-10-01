---
id: m3-01-display-page
milestone: 3
difficulty: 2
depends_on: []
files:
  - coucou/templates/coucou/display.html
  - coucou/locale/fr/LC_MESSAGES/django.po
  - coucou/locale/fr/LC_MESSAGES/django.mo
tests:
  - tests/integration/test_display_page.py
max_diff: 40
---

### Goal
Write the display page's text, in English and French.

### Context
`coucou/templates/coucou/display.html` is the screen on the wall. It has four `{# m3-01: … #}` comments, each marking one place for text. Mum reads it in French from across the room, so keep it short and warm.

The English, exactly:

| Where | Text |
|---|---|
| `loading` section | `<p>{% translate "Just a moment…" %}</p>` |
| `empty` section | `<h1>{% translate "Nothing here yet" %}</h1>` then `<p>{% translate "Photos and notes will appear here." %}</p>` |
| `#reactions` | add `aria-label="{% translate "Send a reaction" %}"` to the existing `<div id="reactions" role="group">` |
| `#offline` | `{% translate "Offline: showing the last moment." %}` |

`"Photos and notes will appear here."` is already translated in `coucou/locale/fr/LC_MESSAGES/django.po`. Translate the other four.

French tone, from strings already on Coucou's screens:
- `"The code works for 10 minutes."` → `"Le code est valable 10 minutes."`
- `"Too many tries for now. Please wait a few minutes and try again."` → `"Trop d'essais d'un coup. Attendez quelques minutes, puis réessayez."`

### Pattern to follow
`coucou/templates/coucou/pair.html`

### Steps
1. Replace each `{# m3-01: … #}` comment in `coucou/templates/coucou/display.html` with its text from the table. Keep every `id`, `data-state` and `hidden` as they are.
2. Add the four new French translations to `coucou/locale/fr/LC_MESSAGES/django.po`, with all their accents. Use `vous` if a sentence needs a person, and a space before `:` as French typography wants.
3. Compile: `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po`. **Copy the English exactly as written above: the tests compare it character for character.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 125
gate_failures: []
tokens: 68504
```
