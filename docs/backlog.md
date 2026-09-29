# Backlog

Nits from reviews and triaged discoveries that aren't scheduled yet. One bullet each: `- [source] description`.

<!-- e.g. - [m1-review nit] Rename `x` to `y` in coucou/ordering.py -->

- [m0] Exercise the headless Claude paths live. Escalation: done in calibration (2 runs, Pro login, cap counted). Still untested: the review loop (M1 review) and the usage-limit pause.
- [m1-review nit, m1-F3] `seed_demo` finds the demo display by label, so renaming it and rerunning creates a second pending display; its "nothing changed" message also ignores `controllers.add(me)`.
- [m2-review nit, m2-F6] `/api/pair/status` is a `POST` with a signed body, but ADR 00 §2.4 and `docs/milestones/m2.md` say `GET`. The milestone doc and `docs/security.md` are fixed; correct ADR 00 the next time an ADR touches the protocol.
- [m2-review nit, m2-F7] `client_ip` (`coucou/pairing.py`) trusts `X-Forwarded-For` from loopback, but uvicorn's `proxy_headers` (`coucou/serve.py`) has already replaced `REMOTE_ADDR` with the forwarded address. Both take the right-most entry, so the result is correct, but the docstring misdescribes production. Keep one mechanism and document it.
- [m1] `runner status` counts only the final run's attempts for a requeued task (m1-01 shows 1, not 3 + 1). Count attempts across runs, e.g. keep the earlier footer when requeuing.
- [owner, M5] Renaming a vault or space slug after photos exist splits the history folder in two. When the history folder is built (M5), make admin either warn and require confirmation, or move the existing folder (and update stored paths) inside the same save.
- [owner, before public launch] Decide the final product name. "Coucou" is taken by several apps (see [`brand/name-check.md`](brand/name-check.md)). Keep it, add a qualifier (e.g. "Coucou Home"), or rename, and run a trademark search first. Settle it before the logo is final and before the native Android wrapper (which needs a package ID).
- [m3-review nit, m3-F8] `coucou/snapshot.py` `build_snapshot`: move the `coucou.ordering` import to the top, and drop the `if moments else None` (`current_content` already returns None for no candidates).
- [m3-review nit, m3-F11] `POST /api/events` takes `"space": true` as space 1, because `bool` is an `int` in Python (`coucou/views/events.py`). Harmless (the space still goes through `reactable_spaces`), but refuse booleans when M4 adds content posts to the view.
- [m3-review nit, m3-F12] Only a device move bumps `auth_generation`. Removing a membership, or moving a space to another vault, in admin reaches open streams at the next 20 s heartbeat, not within 2 s (as documented in `docs/security.md`). Bump in those admin saves (and deletes) too if 2 s should hold for every scope change.
- [ADR 07, future ADR] More than one junior at a time. LM Studio can queue parallel requests, but it's set to no parallel workers, and switching contexts may cost more than it saves. Measure before deciding.
- [ADR 07 item 15, ADR 11 item 3] `display.js` is protected as a whole because it wires the outbox and the stream, so its UI (history arrows, "New ›", the cog) is lead-only work. The next display UI work (e.g. ADR 10's gallery) starts by porting the display to Preact and moving that UI into unprotected modules.
