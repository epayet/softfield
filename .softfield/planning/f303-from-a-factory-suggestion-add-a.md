# F303: A size limit for every Python file, with splits planned, not improvised

The planning thread behind F303's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-25 20:56

> from a factory suggestion: "Add a check that fails when a module in runner/ passes 1,800 lines, or imports a module above it outside a function, so runner/loop.py can't grow back into one file."
>
> but configurable number of lines (why 1800?) and for any python code. i do like the idea to ensuring code files don't get massive, the work around it should make sense logically and within the architecture rather than dumb workarounds

## The lead, 2026-11-25 21:34

> I've drafted ADR 55, the plan and three lead tickets on plan/f303, plus two split cards to plant. The main change from the suggestion: when a file reaches its limit, the ticket that got it there stops, and the split is planned as its own move-only ticket.
>
> 1. **Why 1,800? No reason**: 1,800 was only the size F290 (Split runner/loop.py into one module per job kind) aimed for when it made the new modules. runner/session.py ended at 1,728 lines and is 1,784 now. For comparison, Pylint's default limit is 1,000. So the limit becomes a setting in each project's .softfield/project.toml, and it counts code lines only: blank lines and lines that hold only a comment don't count. That way deleting comments never gets a file under the limit. For Softfield I suggest 1,600 code lines for code and 3,500 for tests. With those numbers, every module that has a sensible shape today still has room, and only the files we already know are too big are over.
>    Action: ADR 55 items 1 to 3; ticket f303-01
> 2. **Any Python code, with tests held to a separate limit**: The check covers every Python file the project tracks in git, except vendored folders. Test files get their own, higher limit: the 'one test file per module' rule makes them 3 to 5 times the size of their module. With a single limit, half the test files would fail, or modules could grow to test-file size. A project that doesn't set the two numbers has no check. Coucou or any other project turns it on by adding two lines.
>    Action: ADR 55 item 1
> 3. **No dumb workarounds: the ticket that hits the limit never does the split**: If a check failing on a retry tells the local model to fix it, the model will cut the file wherever the count passes. That is exactly why ADR 52 (A review leaves the code simpler) turned a size cap down. So when the size check fails, the runner blocks the ticket straight away, whether a developer or the lead was working on it: no retry, no direction, no escalation. The lead's usual look at a blocked ticket then proposes the split on that card's thread: first a ticket that only moves code and changes no behaviour, then the blocked ticket again. You approve the split like any other plan. AGENTS.md says what a split is: cut along what the code does (one module per job kind, per page, per table, as F290 did), the new module gets its own test file, and never a _helpers, _utils or _2 module.
>    Action: ADR 55 items 4 and 5; tickets f303-02 and f303-03
> 4. **I'd drop the import half of the suggestion**: The suggested check allowed an import of a higher module as long as it sits inside a function. That is itself the workaround you don't want: the circular dependency is still there, just hidden. runner/ already has 14 imports like that. A real layer check would also need the layers declared for every project, for a rule nobody has asked for yet. I recommend no import check for now. A review's 'Simpler:' lines can point at those 14 imports when a milestone touches their files.
>    Action: Recorded in ADR 55's 'What doesn't change'
> 5. **This goes back on part of ADR 52 (A review leaves the code simpler)**: Yesterday ADR 52 turned down a file-length cap 'until the numbers show a trend'. They already do: runner/loop.py was 1,487 lines when F290 finished and is 1,756 today. Point 3 answers ADR 52's actual worry, developers splitting files just to pass. ADR 52's review still judges whether each split makes sense.
>    Action: ADR 55, marked as a deviation
> 6. **Files already over the limit: a list that can only shrink**: Five files are over today: runner/requests.py (2,229 code lines), tests/runner/test_loop.py (6,479), tests/factory_dashboard/test_overview.py (5,289), tests/factory_dashboard/test_app.py (4,511) and tests/runner/test_requests.py (3,658). They go on a list in project.toml that the check skips. Once a listed file is under its limit, the check fails until it is taken off the list, so the list empties as the splits land. I'm proposing a card for each kind of split. Splitting the test files may first need a change to the 'one test file per module' rule, because test_loop.py is that big due to the tests that drive the scheduler. That card would decide it.
>    Action: Two cards to plant; ticket f303-01 sets the list
> 7. **Cost and risk**: Three lead tickets, about $3 in total. The risk: a card stops at a block until you approve its split. To make that rare, the planner plans a split first whenever a card's tickets grow a file to within 10% of its limit. runner/loop.py has 62 code lines of room, so the next card that grows it will start with its split. That's the check doing its job.
>    Action: ADR 55 item 6; ticket f303-03
> 8. **Accept the ADR before the plan**: Checking the tickets reports only one problem: they rely on ADR 55, which is still a draft. Once you accept ADR 55, the plan can be approved as it stands. All three tickets go to the lead, because runner/, AGENTS.md and the instructions are protected.
>    Action: Accept ADR 55, then approve the plan
> 9. **No mock-up**: Nothing on screen changes. A blocked ticket's reason shows where every block's reason already shows.
>    Action: nothing
>
> Proposals:
> - ADR 55: Python files have a size limit; a file that reaches it is split by plan (adr)
> - F303: the size check, blocking at once, and how to split (plan)
> - Split runner/requests.py (2,229 code lines, over the 1,600 limit) by what each request does, as F290 split runner/loop.py: one ticket per module that only moves code, the tests moving with it; then take it off the size check's over_limit list. (seed)
> - Split the four test files over the 3,500-line limit (tests/runner/test_loop.py, tests/factory_dashboard/test_overview.py, tests/factory_dashboard/test_app.py, tests/runner/test_requests.py) along their modules; where one module's tests can't fit in one file, propose how the 'one test file per module' rule should bend. (seed)

## The owner, 2026-11-26 00:19

> I sent back your proposal “ADR 55: Python files have a size limit; a file that reaches it is split by plan” (adr-55).
> - On its key point 2 (Code lines only): Disagree comments should count too
> - On its key point 8 (No import-order check): Does that you're suggesting we don't allow imports in a function? I agree

## The lead, 2026-11-26 00:59

> I've revised ADR 55 to answer your two comments, and the plan now has six lead tickets. All six drafts pass checking except for one expected problem: they rely on ADR 55, which is still a draft.
>
> 1. **Comments count: every line counts**: Agreed. Comments and blank lines now count too, so the number is the length an editor shows. Counting comments makes deleting them a way to get a file under the limit. Two other rules in the ADR close that way: no ticket ever trims a file to pass (it is blocked instead), and a planned split never deletes comments. Counting every line also raises the numbers. I now suggest 2,000 lines for code and 4,000 for tests, which leaves runner/session.py 216 lines of room and runner/loop.py 244. The same five files are over as before: runner/requests.py (2,538) and the four big test files.
>    Action: ADR 55 items 2 and 3; ticket f303-01
> 2. **Imports inside a function: forbidden for the project's own code**: I had suggested no import check at all, but your reading is better, so I've taken it. A new check forbids importing the project's own modules inside a function: those imports belong at the top of the file. About 60 such imports exist today, most of them hiding an import cycle; about 20 import runner.milestone. Two kinds of import stay allowed. Imports of other libraries (FastAPI, Playwright) may stay inside a function, because loading a heavy library only when a command needs it is a real reason. Imports under 'if TYPE_CHECKING:' stay too. Today's 60 can't all be removed first without a big refactor. So each file keeps its current count as an allowance, and the count can only go down: one more import in a function fails, and one fewer fails until the allowance is lowered.
>    Action: ADR 55 items 4 and 5; new ticket f303-04
> 3. **A failed import check is fixed by a planned move, as a split is**: When a ticket adds an own-module import inside a function, it is blocked at once, just as for size. The lead then plans the fix: move the shared code down into a module both can import, as a ticket of its own. Copying the function or hiding the import never counts as a fix. The risk is that the dashboard's pages import each other the most (factory_dashboard/overview.py has 15 such imports), so a page ticket is the likeliest to be blocked. To make blocks rare, the planner plans the move first whenever it can see the cycle coming.
>    Action: ADR 55 items 6 to 8; tickets f303-02 and f303-03
> 4. **A card to remove today's hidden imports**: Starting with runner.milestone, which accounts for about a third of them. Each import that goes lowers its file's allowance, until the list is empty.
>    Action: Plant the proposed card
> 5. **Six tickets now, all for the lead**: The two checks (size, then imports); blocking at once, first for developer tickets and then for lead tickets; then the written rules, first how to split and plan ahead, then how to answer a block. Each is one idea, so a fresh session can do it alone. Accept ADR 55 first, then approve the plan: that's the only problem checking the tickets reports.
>    Action: Accept ADR 55, then approve the plan
>
> Proposals:
> - ADR 55: Python files have a size limit and no hidden imports; a ticket that trips either is blocked and the fix is planned (adr)
> - F303: size and import checks, blocking at once, and how to fix (plan)
> - Split runner/requests.py (2,538 lines, over the 2,000 limit) by what each request does, as F290 split runner/loop.py: one ticket per module that only moves code, the tests moving with it; then take it off the size check's over_limit list. (seed)
> - Split the four test files over the 4,000-line limit (tests/runner/test_loop.py, tests/factory_dashboard/test_overview.py, tests/factory_dashboard/test_app.py, tests/runner/test_requests.py) along their modules; where one module's tests can't fit in one file, propose how the 'one test file per module' rule should bend. (seed)
> - Remove the imports of our own modules that sit inside functions (about 60 in runner/ and factory_dashboard/, about 20 of them runner.milestone): move the shared code down to a module both sides can import, one move-only ticket per cycle, and lower each file's allowance in [checks.imports_in_functions] as its imports go. (seed)
