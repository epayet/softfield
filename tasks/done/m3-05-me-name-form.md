---
id: m3-05-me-name-form
milestone: 3
difficulty: 2
depends_on: []
files:
  - coucou/templates/coucou/paired.html
  - coucou/locale/fr/LC_MESSAGES/django.po
  - coucou/locale/fr/LC_MESSAGES/django.mo
tests:
  - tests/integration/test_me_page.py
max_diff: 40
---

### Goal
Write the text of the `/me/` name screen, in English and French.

### Context
`coucou/templates/coucou/paired.html` is the first screen a person sees on their own phone: it asks for the name the family will see. It has five `{# m3-05: … #}` comments, each marking one place for text. Mum reads it in French.

The English, exactly:

| Comment | Text |
|---|---|
| `question` | `{% translate "What should we call you?" %}` |
| `hint` | `{% translate "The others will see this name with your photos and reactions." %}` |
| `button` | `{% translate "That's me" %}` |
| `empty` | `{% translate "Please write a name." %}` |
| `failed` | `{% translate "That didn't work. Please try again in a moment." %}` |

The French for the question is fixed, word for word: `"Comment souhaitez-vous qu'on vous appelle ?"`. Translate the other four.

French tone, from strings already on Coucou's screens:
- `"The code works for 10 minutes."` → `"Le code est valable 10 minutes."`
- `"Too many tries for now. Please wait a few minutes and try again."` → `"Trop d'essais d'un coup. Attendez quelques minutes, puis réessayez."`

### Pattern to follow
`coucou/templates/coucou/display.html`

### Steps
1. Replace each `{# m3-05: … #}` comment in `coucou/templates/coucou/paired.html` with its text from the table. Change nothing else in the file: keep every `id`, `data-state`, `hidden` and `{% if %}`.
2. Add the five French translations to the end of `coucou/locale/fr/LC_MESSAGES/django.po`, with all their accents. Use `vous`, and a space before `?` and `:` as French typography wants.
3. Compile: `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po`. **Copy the English exactly as written above: the tests compare it character for character.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 127
gate_failures: []
tokens: 69793
```
