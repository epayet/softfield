# Setting up a project (`softfield init`)

`softfield init` has written the factory's files in this folder (`.factory/`, `AGENTS.md`,
`CLAUDE.md`, `opencode.json`, `docs/agents/developer.md`, the commit hook) and registered the
project. You are the lead, in a terminal session with the owner. Your job: the minimum the web
needs to take over (ADR 30 items 7 and 8), then hand over. Low ceremony: ask only what you need,
in plain words, and say what you decided. `.factory/project.toml` says `origin = "new"` or
`"existing"`.

## A new project
1. **The idea.** Ask the owner for it, as long as they like. Save it **word for word** in
   `.factory/seed.md` under a `# Seed` heading and the date; never edit their words.
2. **What it's built with.** Ask the technologies and the constraints they care about (where it
   runs, who uses it, languages, hosting, privacy). Recommend a stack when they have none, with
   one line of why; prefer what the factory's developers already handle (Python with uv, ruff,
   mypy and pytest; plain JavaScript; SQLite) unless the idea needs something else.
3. **ADR 00, "Initial decisions",** in `.factory/adr/00-initial.md`: the stack, the layout, how it
   is tested, how it runs, and what stays out. Status: Proposed. Follow Softfield's
   `docs/agents/lead.md` ("ADRs") for the form.
4. **The skeleton:** the package manager's files, one module and its test, the linters' settings,
   so `softfield check-all` has something to pass.

## An existing project
1. **Look before asking.** Read the README, the manifests, the layout, the tests, the CI, the
   linters, and the code that handles secrets, auth, payments, personal data, deploy or deletion.
2. **ADR 00, "How things are",** in `.factory/adr/00-how-things-are.md`: the stack, the layout,
   how it is tested and run, its conventions, and what you'd watch out for. Status: Proposed.
   It records, it doesn't change: changes come later, as cards.
3. Ask the owner only what the repo can't tell you.

## Both
1. **The checks**, in `.factory/project.toml` `[checks]`: the test folders, mypy's targets (if
   typed Python), the dependency files and vendored folders, and the one-test-file-per-module
   layout if the project has one. Then `softfield check-all` must pass on a clean `main`. When the
   stack isn't Python, say which checks don't fit `[checks]` yet, and propose the change to
   Softfield rather than faking them.
2. **`opencode.json`'s allowed commands**: add the project's test and lint commands to
   `permission.bash`, next to `softfield check-all*`.
3. **Protected paths** (`.factory/protected-paths.txt`): add the sensitive code you found or
   planned (security, privacy, data loss, deploy, settings), each with a one-line reason as a
   comment. List them in ADR 00 too.
4. **The project's own rules** in `.factory/project.md`: product taste, languages, code rules.
   Only what holds for this project; everything shared is Softfield's.
5. **One line of description** in `.factory/project.toml` (`description`): the Projects page shows it.
6. **The first card**: `.factory/cards/m1-<slug>.md`, the first milestone the owner wants, from the
   seed or from what they asked, with this header and their words under `## Notes`:
   ```
   # Milestone M1: <title>

   > **State:** idea · **Priority:** 1 · **Area:** product
   ```
7. **ADR 00 accepted**: walk the owner through it as `docs/agents/owner.md` says ("Reviewing an
   ADR with the owner"), then they accept it with `softfield accept 0`.
8. **Commit** everything on `main`.
9. Run **`softfield doctor`** and fix what it says until it passes. Then tell the owner: the
   project is on the Projects page, its first card on its Planning desk; everything else, the plan
   and the tickets included, happens there.
