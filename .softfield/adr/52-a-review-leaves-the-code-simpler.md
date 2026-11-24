# ADR 52: A review leaves the code simpler, and suggests the features that follow

- **Status:** Accepted (by the owner, 2026-11-24)
- **Date:** 2026-11-23
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** `docs/workflow.md` "Milestone review loop" (what a review looks for), `runner/instructions/lead.md` "Review", `prompts.REVIEW` and `prompts.PLANNER` (`runner/prompts.py`). Builds on [ADR 43](43-the-owner-plants-a-reviews-fixes.md) (quoted lines to plant).
- **Evidence:** F286 (owner, 2026-11-21): "I want to make sure that we're making the product and the factory less complex over time, not more. Boy scout rule."
  - The review brief asks for bugs, weak tests, the French and the mock-up; nothing asks it to look for complexity. Of the 23 quoted "What next" lines in `.softfield/reviews/`, one is a simplification (F264's dead 5-hour wait machinery in `runner/loop.py`); the rest are bugs, test speed and process.
  - `runner/loop.py` is 6,565 lines. Since 2026-10-23, 41 commits added 1,411 lines to it and removed 497: about three lines in for one out. `runner/requests.py` is 2,427, `factory_dashboard/queries.py` 1,379, `runner/metrics.py` 1,371.
  - Nothing in a review's numbers shows whether a milestone grew the code or shrank it.
  - Owner, on F286's thread (2026-11-24): "the review should also suggest product features related to what it just done. and in the case of the softfield project, softfield is the product. the French looks oddly specific, probably a remnant of coucou?" Softfield's reviews write "**Product:** on hold, as you asked" (F100, F101, F103, F104, F106 and more): they read Product as Coucou. `prompts.REVIEW` ends its test line with "Check the French." for every project; F280 (The factory's instructions name no project) removes the same rule from `lead.md` but not from `prompts.py` or `docs/workflow.md`.

## Decisions (⚑ = deviates from an earlier decision)
1. **Every review looks for complexity, after correctness.** In the milestone's diff and the files it touched: code that repeats a helper that already exists, dead code, settings or branches left behind, a second way of doing what one way already does, a function or file grown past one job, a new rule where changing an old one would have done.
2. **Complexity the milestone added is a should-fix on its own work** (the Boy Scout rule): routed as any should-fix today (a developer fix ticket by default, the lead when small or protected). A milestone doesn't leave the code more tangled than its plan needed.
3. **⚑ Older complexity in the files it touched is a quoted line starting "Simpler:"** under "6. What next" (ADR 43's `later` route): one sentence naming the file, what to remove or merge into what, and about how many lines it saves. **At most two per review**, the ones that save the most, so the plate doesn't fill with taste. Files the milestone didn't touch are left out. This narrows ADR 43 item 1 for this kind of finding only: no ticket is written for it.
4. **The review's numbers show the code's size change.** `softfield report <key>` adds one row, "Code lines", the added and removed lines of the milestone's merged tickets, leaving out `tests/`, `docs/`, `.softfield/` and Markdown; and a "Net code lines" column in its Trends table. Computed from git each time, nothing stored. The sheet's "What changed" says it in words when the net is negative.
5. **A plan says what it reuses or retires.** When a card adds a mechanism (a module, a table, a setting, a job kind, a page), the planner's Decisions name what existing code it builds on, and what it makes removable; a removal is a ticket in the same plan.
6. **A review suggests the features that follow from what it just built:** at most two quoted lines under "6. What next", each one a feature the owner could plant, in their voice, building on the milestone's work (not a fix: fixes are items 2 and 3). None when nothing follows naturally.
7. **⚑ On the factory's own project, the factory is the product.** Its review writes no Product bullet ("on hold" meant Coucou): Softfield's features, "Simpler:" lines and fixes all go under Factory, which plants on Softfield's board as ADR 43 item 2 says. In any other project, Product is that project and Factory is what Softfield should learn. This replaces the reading of ADR 43 item 2 that left Softfield's reviews with an empty Product.
8. **No project's language check is in the package.** The review's "Check the French." goes, in `prompts.REVIEW` and `docs/workflow.md`, as F280 does in `lead.md`: a project's review reads its own `.softfield/project.md`, which is in the review's system prompt, for its language rules. Coucou's line is kept under F280's "For Coucou".

## What doesn't change
- Checkpoints still look for bugs only: a refactor finding there would go to the local developer as a fix ticket, the costliest place to argue taste.
- The owner still plants a quoted line or not, press by press (ADR 43 item 3). "Simpler:" is the sentence's first word, not a new kind of line: the review page and its Plant buttons work as they are.
- No metric gate: a milestone that grows the code is not refused. Lines are a rough measure of complexity, read beside the review's judgement, never a pass or fail.

## Alternatives turned down
- **A complexity gate (radon, a file-length cap):** it fails good work for a number, and the developers would split files to pass it. Turned down until the numbers in item 4 show a trend worth a gate.
- **The review fixes old complexity itself:** a refactor of untouched-by-plan code inside a review pays Opus to change code no ticket asked for, and widens what the owner signs off.
- **A "Simpler" mark on the review page:** a mock-up and a UI ticket for a word the sentence already starts with. Kept for later if the owner wants them to stand out more.

## Consequences
- **Cost:** a little more review reading (no extra job); a few more should-fix tickets on milestones that add duplicates, paid once instead of carried forever.
- **Risk:** taste dressed up as findings. Items 2 and 3 limit it: on the milestone's own work only as should-fix, at most two quoted lines on older code.
- **Risk:** feature ideas grow the board, and more features mean more code: the opposite of this ADR. Item 6 caps them at two, and the owner plants only what they want; the planner's item 5 then asks each what it retires.
- Large refactors (splitting `runner/loop.py`) are architecture: they come to the owner as a card, never from a review alone.
