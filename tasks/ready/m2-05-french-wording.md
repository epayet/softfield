---
id: m2-05-french-wording
milestone: 2
depends_on: []
files:
  - coucou/locale/fr/LC_MESSAGES/django.po
  - coucou/locale/fr/LC_MESSAGES/django.mo
tests:
  - tests/integration/test_french_wording.py
max_diff: 40
finding: m2-F2
---

### Goal
Reword nine French translations of the pairing screens so they read warmly and plainly.

### Context
In `coucou/locale/fr/LC_MESSAGES/django.po`, change only the `msgstr` of these `msgid`s. Never change a `msgid`. Copy each new text exactly, including accents, apostrophes and the space before `!` and `:`.

| msgid | new msgstr |
|---|---|
| They'll check that these letters match on their screen: | Elle vérifiera que ces caractères s'affichent aussi sur son écran : |
| This browser can't connect to Coucou. Try an up-to-date Chrome or Safari. | Ce navigateur ne peut pas se connecter à Coucou. Essayez avec une version récente de Chrome ou de Safari. |
| Too many tries for now. Please wait a few minutes and try again. | Trop d'essais d'un coup. Attendez quelques minutes, puis réessayez. |
| Lots of devices are waiting to be connected. Please try again later. | Beaucoup d'appareils attendent déjà d'être connectés. Réessayez un peu plus tard. |
| Can't reach Coucou right now. It will keep trying. | Impossible de joindre Coucou pour le moment. Cet appareil va continuer d'essayer. |
| Something went wrong. | Oups, un problème est survenu. |
| All set! | C'est prêt ! |
| You're connected! | Ce téléphone est connecté ! |
| Soon you'll be able to send moments from here. | Bientôt, vous pourrez envoyer des moments depuis ce téléphone. |

### Pattern to follow
`coucou/locale/fr/LC_MESSAGES/django.po`

### Steps
1. In `django.po`, replace the nine `msgstr` values with the new texts above. Leave every other line as it is.
2. Compile it: `msgfmt -o coucou/locale/fr/LC_MESSAGES/django.mo coucou/locale/fr/LC_MESSAGES/django.po`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
