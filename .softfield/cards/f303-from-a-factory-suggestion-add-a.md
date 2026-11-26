# Milestone F303: A size limit for every Python file, with splits planned, not improvised

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-25.

## Notes
from a factory suggestion: "Add a check that fails when a module in runner/ passes 1,800 lines, or imports a module above it outside a function, so runner/loop.py can't grow back into one file."

but configurable number of lines (why 1800?) and for any python code. i do like the idea to ensuring code files don't get massive, the work around it should make sense logically and within the architecture rather than dumb workarounds

## Plan (lead, 2026-11-25)
- **Why:** `runner/loop.py` went from 1,487 lines at F290's end to 1,756 the same day; `runner/requests.py` is 2,538. About 60 imports of the project's own modules hide inside functions to dodge import cycles. Nothing stops either growing, and ADR 52's review only notices after the fact.
- **The rule is [ADR 55](../adr/55-a-file-at-its-size-limit-is-split-by-plan.md):** a configurable size check for every Python file, every line counted; no import of the project's own modules inside a function; a ticket that trips either is blocked and the fix is planned, never improvised.
- **Revised with the owner (2026-11-26):** comments count (every line does); the import check forbids own-module imports in functions, with today's counted down to zero.
- **Tickets** (all lead: `runner/`, `AGENTS.md` and the instructions are protected): the two checks, then blocking at once (developer tickets, then lead tickets), then the written rules (how to split and plan ahead; how to answer a block). Listed under "Tickets".
- **No mock-up:** nothing on screen changes; a blocked ticket's reason shows where every block's reason already does.

## Decisions
- **D1: size settings,** in `Checks` (`runner/config.py`), read from `[checks]` of `.softfield/project.toml`: `max_lines: int = 0`, `max_test_lines: int = 0` (0 = no check), `over_limit: tuple[str, ...] = ()` (repo-relative paths). Softfield's `project.toml` sets 2,000, 4,000 and `over_limit = ["runner/requests.py", "tests/runner/test_loop.py", "tests/factory_dashboard/test_overview.py", "tests/factory_dashboard/test_app.py", "tests/runner/test_requests.py"]`.
- **D2: the size check,** `size_problems(repo: Path) -> list[str]` in `runner/gates.py`, beside `layout_problems`, over `git ls-files '*.py'` less `dependency_dirs`; every line counts (`len(text.splitlines())`). A file under one of `test_dirs` takes `max_test_lines`, any other `max_lines`. One line per problem: `<path>: <n> lines, over the limit of <m>`, or `<path>: <n> lines, under the limit of <m>: remove it from over_limit`. check-all's check and the gate are both named `size`, right after `layout`.
- **D3: import settings:** `imports_at_top: bool = False` and `imports_in_functions: Mapping[str, int]` (from `[checks.imports_in_functions]`, path → today's count). The project's own modules are the top-level names of its tracked Python files and packages (`runner`, `factory_dashboard`, `tests` here).
- **D4: the import check,** `import_problems(repo: Path) -> list[str]` in `runner/gates.py`, with `ast`: an `Import` or `ImportFrom` of an own module (or a relative one) anywhere but the module's top level counts, except under `if TYPE_CHECKING:`. A file's count over its allowance (0 when unlisted) is `<path>:<line>: imports <module> inside a function (<n> here, <m> allowed)`, naming each such line; a count under its allowance is `<path>: <n> imports in functions, <m> allowed: lower it to <n>`. Named `imports`, right after `size`.
- **D5: a structure failure blocks at once** (ADR 55 item 6): in `run_task` (`runner/developer_job.py`) when the attempt's `size` or `imports` gate fails, and in the lead ticket's settling (`runner/lead_job.py`) when either is among check-all's failures, the ticket goes through `block` with the check's first problem line and "it needs a planned split" (size) or "it needs a planned move of the shared code" (imports); the branch keeps the work. No retry, direction, step-up or escalation.
- **D6: builds on** `Checks`, `layout_problems`'s shape, `block` and ADR 29's look; **makes removable:** nothing in the code now (F290 D8's sizes were a plan, not a setting); the `# runner.x imports this module` comments go with their imports, in the removal card.

## Tickets
- f303-01-size-check (lead)
- f303-04-imports-at-top (lead): after 01
- f303-02-size-blocks-at-once (lead): developer tickets, after 04
- f303-02-checks-block-at-once (lead): lead tickets, after the one above
- f303-03-how-to-split (lead): what a split or a move is (`AGENTS.md`) and planning it ahead (`lead.md`, `prompts.PLANNER`), after 04
- f303-03-how-to-fix (lead): never working around a block, and answering one with a move-only ticket first, after the one above
