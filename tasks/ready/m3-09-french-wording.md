---
id: m3-09-french-wording
milestone: 3
depends_on: []
files:
  - coucou/locale/fr/LC_MESSAGES/django.po
  - coucou/locale/fr/LC_MESSAGES/django.mo
tests:
  - tests/integration/test_french_wording.py
max_diff: 30
finding: m3-F5
---

### Goal
Reword six French translations of the display and `/me/` screens so they read warmly and plainly.

### Context
In `coucou/locale/fr/LC_MESSAGES/django.po`, change only the `msgstr` of these `msgid`s. Never change a `msgid`. Copy each new text exactly, including accents, apostrophes, the `…` character and the space before `:`.

| msgid | new msgstr |
|---|---|
| Just a moment… | Un petit instant… |
| Nothing here yet | Rien pour l'instant |
| Offline: showing the last moment. | Hors ligne : voici le dernier moment. |
| The others will see this name with your photos and reactions. | Les autres verront ce prénom à côté de vos photos et de vos réactions. |
| Please write a name. | Écrivez votre prénom. |
| That didn't work. Please try again in a moment. | Ça n'a pas marché. Réessayez dans un instant. |

### Pattern to follow
`coucou/locale/fr/LC_MESSAGES/django.po`

### Steps
1. In `django.po`, replace the six `msgstr` values with the new texts above. Leave every other line as it is.
2. Compile it: `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
