# Milestone F204: Publish Softfield as a versioned package, with CI

> **State:** idea · **Priority:** 100 · **Area:** factory
> From the owner's terminal session of 2026-11-02.

## Notes
"I eventually want softfield to be a published package with ideally some CI to publish new versions."

Groundwork done on 2026-11-02: the instructions ship in the package, and a clean install finds them. `softfield` was free on PyPI that day. Open:
- A GitHub Action on a version tag: run the checks, publish with trusted publishing (no stored password).
- Whether the suite passes off this machine: it has never been tried.
- Numbered versions, and `doctor` saying when a newer one exists (the owner's question of 2026-10-27 on F127).
- The top-level names `runner` and `factory_dashboard` are too generic for a public package: `softfield.runner` and so on. It's the one rename to reopen, here only.
- `docs/workflow.md` is cited by tickets and isn't in the package.
- The author's opinions (`runner/instructions/author/`) ship as an example; when others use it, whether they move to `~/.config/softfield/`.
