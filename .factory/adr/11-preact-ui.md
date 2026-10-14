# ADR 11: One UI setup everywhere: Preact + htm

- **Status:** Accepted (by the owner, 2026-09-29; each item as chosen in conversation)
- **Date:** 2026-09-29
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

ADR 00 planned Django templates plus Alpine.js for the sender screens, and plain ES modules for the display. M3 built the display with plain modules: every string in the template, and `render.js` showing and hiding `data-state` sections. Alpine was never vendored.

Planning M4 (the sender app), the owner said three things:
- **The app will get more complex over time,** and React may come one day.
- **One setup everywhere:** not a framework in one app and none in the other.
- **Juniors have no web fetch** (`opencode.json` denies `webfetch` and `websearch`). Would docs help them?

The options compared:

| Option | Growth path |
|---|---|
| Plain modules everywhere (today) | Grows into a home-made mini-framework. |
| Alpine everywhere | Enhances server-rendered HTML. Moving to React later would be a rewrite of the UI layer. |
| **Preact + htm everywhere** | React's component and hooks API. Moving to React later is mostly changing imports. |
| React itself | Needs a bundler: React 19 ships no browser-ready module files, and CDNs are ruled out (AGENTS.md rule 7). |

## Decisions

### 1. ⚑ Preact + htm for all UI

Amends ADR 00 §1 (Frontend: "Alpine.js (sender)").
- **The file:** htm's single standalone file (`htm/preact/standalone.module.js`: Preact, hooks and htm in one ES module), vendored at a pinned version, with its licence, at `coucou/static/coucou/vendor/preact-htm.js`. It's a protected path.
- **No build step and no import map:** the CSP (`script-src 'self'`) would block an inline import map. Modules import the vendored file by relative path.
- **Components** are plain `.js` modules in `coucou/static/coucou/js/`, one concept per module, each with its browser test (`tests/browser/test_<name>.py`, as today).
- **Plumbing stays plain modules:** auth, crypto, pairing, the outbox, the live stream and the service workers. Components call them.

### 2. ⚑ Text lives in the JS, through Django's catalogue

This is what ADR 00 A2 first planned, and M3 never needed.
- JS strings use `gettext()` / `interpolate()` from Django's `JavaScriptCatalog`, served by the public app at `/jsi18n/`, in the device's language.
- The French goes in `coucou/locale/fr/LC_MESSAGES/djangojs.po` and its compiled `.mo`. The `translations` gate and `tests/integration/test_translations.py` cover it, as they cover `django.po`.
- The service workers cache `/jsi18n/`, so French works offline.
- If `xgettext` can't read `gettext()` inside htm templates, strings go in constants at the top of the module. The first screen (M4, L0) settles which.
- Junior note 3 ("text lives in the template, never in the JS") is rewritten to match.

### 3. The display moves at its next UI change

- **M4** builds the sender in Preact. The display stays as it is until its next UI work.
- **That work** starts with porting the display (ADR 10's gallery, for example). The port also moves the browsing UI out of the protected `display.js` (ADR 07 item 15).
- Until then there are two setups, on purpose and for a limited time.

### 4. Juniors learn Preact from the repo, not the web

- `docs/agents/preact.md` is a one-page reference, pinned to the vendored version: htm syntax, the hooks we use, `onInput` rather than React's `onChange`, `gettext`, our patterns and pitfalls. The first screen, built by the lead, is the worked example (ADR 07 item 3).
- Web fetch stays denied, because:
  - a documentation page can take tens of thousands of tokens of the junior's ~180k context
  - live docs describe the latest version, not the one we pin
  - fetched pages are untrusted text reaching an agent that edits the repo

  Enabling it would need its own ADR, for example as a logged experiment on one stretch ticket.

## Consequences

- One vendored file (about 5 KB gzipped) and one new public URL, `/jsi18n/`.
- Page templates become thin shells: a mount point plus the page's data as `json_script`.
- Browser tests mount components on the harness page, with `gettext` stubbed. The French is checked by the gates and at review.
- A future move to React needs a build step. That's a separate decision, taken when it's worth it.
