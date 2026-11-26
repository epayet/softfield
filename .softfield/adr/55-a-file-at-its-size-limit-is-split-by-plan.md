# ADR 55: Python files have a size limit and no hidden imports; a ticket that trips either is blocked and the fix is planned

- **Status:** Accepted (by the owner, 2026-11-26)
- **Date:** 2026-11-25 (revised 2026-11-26 with the owner)
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** `docs/workflow.md` "Gates" (two new checks), `AGENTS.md` item 5, `runner/instructions/lead.md` "Plan" and "Tickets", `prompts.PLANNER` (`runner/prompts.py`), `.softfield/project.toml` `[checks]`. Narrows [ADR 52](52-a-review-leaves-the-code-simpler.md)'s "Alternatives turned down" (a file-length cap). Builds on the `layout` check (`runner/gates.py`, `layout_problems`) and the lead's look at a blocked ticket ([ADR 29](29-the-lead-looks-at-a-blocked-ticket.md)).
- **Evidence:**
  - F290 (Split runner/loop.py into one module per job kind) took `runner/loop.py` from 6,813 lines to 1,487 on 2026-11-25; it was 1,756 the same evening. `runner/session.py` landed at 1,728 and is 1,784.
  - F290's review suggested: "Add a check that fails when a module in runner/ passes 1,800 lines, or imports a module above it outside a function". The owner, on F303 (2026-11-25): "configurable number of lines (why 1800?) and for any python code … the work around it should make sense logically and within the architecture rather than dumb workarounds".
  - 1,800 has no reason behind it: it was F290 D8's landing target for the new modules. Pylint's default is 1,000 lines.
  - Today, in lines: `runner/requests.py` 2,538; `runner/session.py` 1,784; `runner/loop.py` 1,756; every other module under 1,450. Tests: `tests/runner/test_loop.py` 7,813, `tests/factory_dashboard/test_overview.py` 6,251, `tests/factory_dashboard/test_app.py` 5,511, `tests/runner/test_requests.py` 4,304; every other test file under 3,500.
  - About 60 imports of the project's own modules sit inside a function in `runner/` and `factory_dashboard/`, most with a comment like `# runner.milestone imports this module`: each hides an import cycle. About 20 of them are `runner.milestone`, imported by the loop and the jobs it imports. A few are on purpose: `runner/cli.py` and `runner/look.py` load the dashboard (and FastAPI) only for the command that needs it.
  - ADR 52 turned a file-length cap down because "the developers would split files to pass it". Item 6 answers that: no ticket ever fixes a structure check itself.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ A `size` check, in check-all and the gates, beside `layout`.** It fails when a Python file the project tracks in git (outside `dependency_dirs`) is over its limit. Two limits in `[checks]` of `.softfield/project.toml`: `max_lines` for code and `max_test_lines` for files under `test_dirs` (one test file per module makes them several times their module's size). A project without them has no check; any project, not just Softfield, turns it on with two lines.
2. **Every line counts** (owner, 2026-11-26): comments and blank lines too, as an editor shows the file. The way under the limit that this leaves, deleting comments, is closed by item 6 (no ticket trims a file) and item 7 (a split never deletes comments).
3. **Softfield's limits: 2,000 lines for code and 4,000 for tests.** Set where today's well-shaped modules have room (`runner/session.py` 216 lines, `runner/loop.py` 244) and only the files already known to be too big are over. They change in `project.toml` like any cap (an Accepted ADR).
4. **An `imports` check: no import of the project's own modules inside a function** (owner, 2026-11-26). An import of the project's own code sits at the top of the file. Inside a function, or anywhere but the top level, it fails the check, unless it is under `if TYPE_CHECKING:`. Imports of other packages (FastAPI, Playwright, the standard library) may stay inside a function: loading a heavy library only when it's needed is a reason, not a workaround. On with `imports_at_top = true` in `[checks]`.
5. **Today's imports are counted, and the counts only go down.** `[checks.imports_in_functions]` gives each file that has them its count today. A file over its count fails; a file under it fails until its count is lowered, so the table empties as cycles are removed. The two deliberate ones (`runner/cli.py`, `runner/look.py` loading the dashboard) stay listed.
6. **A ticket never fixes a structure check itself.** When `size` or `imports` fails, the runner blocks the ticket at once, developer or lead, with no retry, direction or escalation, and a reason that names the file and what it needs: a planned split, or a planned fix of the cycle. The lead's look at the blocked ticket (ADR 29) proposes the fix on the card's thread: a move-only lead ticket first, the blocked ticket brought back after it. The owner approves it like any plan.
7. **What a fix is** (written in `AGENTS.md` item 5, for anyone): a file is split by what it does, along the edges the code already has (one module per job kind, per page, per table, as F290 and F143 did); the new module is named for its job and gets its own test file (item 9); the move changes no behaviour (F290 D2). Never a `_helpers`, `_utils`, `_2` or `_part` module, never code moved only to fit, never comments deleted. A cycle is fixed by moving the shared code down to the module both can import, never by copying it or hiding the import.
8. **The planner plans ahead.** A plan whose tickets grow a file within 10% of its limit, or need code from a module that imports theirs, puts the split or the move first, as its own move-only lead ticket, so the block in item 6 is the backstop and not the usual way.
9. **Files already over are listed, and the list only shrinks.** `[checks] over_limit` names them (today: `runner/requests.py` and the four test files above). A listed file isn't checked for size; a listed file under its limit fails the check until it leaves the list.

## What doesn't change
- ADR 52's review still judges complexity, and still looks at whether a split or a move made sense: a "file grown past one job" is a finding, at any size.
- `max_diff` stays a backstop against rewritten files; it is not a size rule.
- No declared layer order ("which module may import which"): with imports at the top (item 4), a cycle mostly fails as soon as the code loads (a `from x import y` of a name not yet defined), so the order stays one way without writing it down. A cycle of plain `import x` lines can still load; the review catches those.

## Alternatives turned down
- **The developer fixes the check on a retry, with a hint:** the local model would cut the file at the line that passes, or copy the function it can't import. This is ADR 52's objection, and the owner's.
- **The lead fixes it inside the ticket that tripped it:** a move mixed into a feature's diff can't be reviewed as move-only, and the fix's shape isn't approved by anyone.
- **Code lines only (no comments, no blanks):** turned down by the owner; item 6 closes the trimming it would have prevented.
- **Removing today's 60 hidden imports first:** a refactor of the loop, the jobs and the dashboard's pages before the check can start. The counts in item 5 stop new ones today; their removal is its own card.
- **import-linter's layer contracts:** a new dependency and a declared layer list, where item 4 gets most of it from Python itself.

## Consequences
- **Cost:** four lead tickets (about $4), a split card for each listed file and a card to remove the hidden imports, when the owner plants them.
- **Risk:** a card stops on a block until the owner approves its fix. Item 8 makes that rare; when it happens, the card's thread says why and what to approve. The dashboard's pages import each other most (`factory_dashboard/overview.py` has 15), so a page ticket is the likeliest to trip `imports`.
- **Makes removable:** F290 D8's one-off sizes, which become the check's settings; the `# runner.x imports this module` comments as their imports go.
