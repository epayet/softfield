---
id: m3-11-display-texts
milestone: 3
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
Write the text for the display's new arrows, "New" hint and settings cog, in English and French.

### Context
`coucou/templates/coucou/display.html` is the screen on the wall. It has six `{# m3-11: … #}` comments, each marking one place for text. Mum reads it in French from across the room.

The English, exactly:

| Comment | Text |
|---|---|
| `previous` (an `aria-label`) | `{% translate "Previous moment" %}` |
| `next` (an `aria-label`) | `{% translate "Next moment" %}` |
| `new` (before ` ›`) | `{% translate "New" %}` |
| `settings` (an `aria-label`) | `{% translate "Settings" %}` |
| `language` | `{% translate "Language" %}` |
| `close` | `{% translate "Close" %}` |

A "moment" is a post (a photo or a note): masculine in French, "un moment".

French tone, from strings already on Coucou's screens: short, plain and warm, never "Veuillez".
- `"Just a moment…"` → `"Un petit instant…"`
- `"That didn't work. Please try again in a moment."` → `"Ça n'a pas marché. Réessayez dans un instant."`

### Pattern to follow
`coucou/templates/coucou/display.html` itself: see how `aria-label="{% translate "Send a reaction" %}"` is written.

### Steps
1. Replace each `{# m3-11: … #}` comment in `coucou/templates/coucou/display.html` with its text from the table. Inside `aria-label="…"`, the tag goes between the quotes. Keep ` ›` after "New". Change nothing else: keep every `id`, `hidden`, `data-language` and the words "English" and "Français" as they are.
2. Add the six French translations at the end of `coucou/locale/fr/LC_MESSAGES/django.po`, with all their accents.
3. Compile: `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po`. **Copy the English exactly as written above: the tests compare it character for character.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
