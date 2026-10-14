# Milestone F129: Coucou's translations check is a copy

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

The translations gate (`runner/i18n.py`) is Django gettext for Coucou: it runs
`manage.py makemessages` and checks `coucou/locale/`. When Coucou left the factory's repo, its
integration test needed it, so Coucou got a copy (`coucou/i18n_checks.py`); the gate in Softfield
still runs the runner's copy when a project's `[checks] translations = true`.

ADR 30 item 3 planned it as one of Coucou's own check commands. Do that with the "any stack"
card's check commands: Coucou names its translations command, the runner's Django code goes,
and the two copies become one. Coucou's product work is on hold, so this waits for that card.
