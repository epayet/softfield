# F286: Reviews look for complexity and leave the code simpler (Boy Scout rule)

The planning thread behind F286's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-21 05:04

> I want code reviews to highlight refactoring and reduce complexity opportunities when it finds them. The cards suggested to plant at the review page kind of do this already. I want to make sure that we're making the product and the factory less complex over time, not more. Boys scout rule

## The lead, 2026-11-23 22:35

> I've drafted ADR 51 plus two lead tickets for F286. The only problem `softfield check-tickets` reports for them is that ADR 51 still needs your acceptance.
>
> 1. **You're right that reviews barely do this today**: The review brief (runner/prompts.py, REVIEW) asks for bugs, weak tests, the French and the mock-up. It never asks about complexity. Of the 23 ideas to plant across all the reviews, only one simplifies anything: F264's dead 5-hour wait code in runner/loop.py. The rest are bugs, test speed and process. Meanwhile runner/loop.py is 6,565 lines. In the last month it gained 1,411 lines and lost 497 over 41 commits, about three lines in for every one out.
>    Action: ADR 51 and the two tickets below.
> 2. **How the Boy Scout rule works in a review**: Every review looks for complexity after it checks correctness: a repeat of a helper that already exists, dead code or settings left behind, two ways of doing one thing, a function that does too many jobs. If the milestone itself added it, it's a should-fix and gets fixed like any other (a developer ticket, or me when it's small). If it was already there in a file the milestone touched, it becomes an idea to plant starting with "Simpler:". There are at most two per review, the ones that save the most lines, so your review page doesn't fill up with matters of taste.
>    Action: Ticket f286-01 (lead: runner/prompts.py is protected).
> 3. **Is it getting simpler over time? A number to check**: Each review's numbers get a 'Code lines' row: lines the milestone added and removed, leaving out tests, docs and Markdown. The table of earlier milestones gets a 'Net code lines' column. It's worked out from git each time, nothing is stored, and it never fails a milestone. Line counts only roughly measure complexity, but they're the one thing that shows a trend. If you later want this on the weekly report (F59, A weekly report page), it's one extra number there.
>    Action: Ticket f286-02 (lead).
> 4. **Complexity starts at planning, so the plan answers too**: Most complexity is decided in a plan, before any review sees it. So when a card adds a new piece (a module, a table, a setting, a job kind, a page), its plan will name what existing code it builds on and what it makes removable. A removal becomes a ticket in the same plan. It's one sentence in the planner's brief, built in f286-01.
>    Action: ADR 51 item 5.
> 5. **Pushback: no complexity gate, and checkpoints stay as they are**: I'd turn down a hard check such as a file-length cap or a complexity score. It would fail good work over a number, and developers would just split files to get past it. I'd also keep refactoring out of checkpoints, because their findings go to the local developer as fix tickets, the costliest place to argue about taste. If the numbers from point 3 show the code keeps growing, a gate can come later through an ADR.
>    Action: Nothing; this is in ADR 51 under 'What doesn't change'.
> 6. **No mock-up: nothing on screen changes**: "Simpler:" is just the first word of an ordinary idea to plant, so the review page and its Plant buttons work as they are. If you want these ideas marked out (a badge or their own group), say so and I'll draw it.
>    Action: Nothing unless you ask for the mark.
> 7. **The Boy Scout rule won't fix runner/loop.py on its own**: Small cleanups won't shrink a 6,565-line file. Splitting it changes the code's layout, which is your call, so it should be its own card, not something a review decides. If you want it, paste this into Plant: "runner/loop.py is 6,500 lines and grows three lines for every one removed: plan splitting it by job kind (developer tickets, lead tickets, planner, reviews, waits) with no change in behaviour, one module per ticket."
>    Action: An idea for you to plant if you want it.
> 8. **Accept ADR 51 first, then approve the plan**: Both tickets depend on ADR 51, and Approve won't take the plan while the ADR is still Proposed. Neither ticket depends on the other, so each can be picked as soon as it's queued. Since F286 starts as an idea with nothing queued, there's no need to pause the factory.
>    Action: Accept ADR 51, then approve the F286 plan.
>
> Proposals:
> - ADR 51: A review leaves the code simpler than it found it (adr)
> - F286: reviews look for complexity, and their numbers show code growth (plan)

## The owner, 2026-11-24 08:26

> On point 1: the review should also suggest product features related to what it just done. and in the case of the softfield project, softfield is the product.the French looks oddly specific, probably a remnant of coucou ?

## The lead, 2026-11-24 13:20

> I've added both of your comments to ADR 51 and ticket f286-01. `softfield check-tickets` now reports only one problem for F286's tickets: ADR 51 still needs your acceptance. The two problems it lists for F9 are on that card's tickets, not this plan's.
>
> 1. **Reviews will suggest features, not just fixes**: Agreed. A review's "6. What next" will carry at most two feature ideas that build on what the milestone just made, each a sentence you can plant. One catch: more features means more code, the opposite of what this card is for. So I cap them at two, and when you plant one, its plan has to say what it retires (ADR 51 item 5).
>    Action: ADR 51 item 6; built in f286-01.
> 2. **On Softfield, Softfield is the product**: You're right, and the reviews show it: F100, F101, F103, F104, F106 and more all write "Product: on hold, as you asked". They read Product as Coucou. From now on, a Softfield review has no Product bullet. Its features, "Simpler:" ideas and fixes all go under Factory, which plants on Softfield's board. Other projects keep both: Product is that project, and Factory is what Softfield should learn from it. The ideas you plant from the review page work as they do now.
>    Action: ADR 51 item 7 (a change to ADR 43 item 2, so it's flagged); built in f286-01.
> 3. **The French is left over from Coucou**: Yes. F280 (The factory's instructions name no project) already removes it from lead.md and keeps Coucou's wording for Coucou's own rules. But it misses two places: the review brief in runner/prompts.py ends with "Check the French." for every project, and docs/workflow.md says "and the French". f286-01 removes both and now waits for F280's ticket, so the two don't edit the same lines at once. Any project that needs a language check writes it in its own .softfield/project.md, which every review already reads.
>    Action: ADR 51 item 8; f286-01 now waits for f280-01.
> 4. **Still to do: accept ADR 51, then approve the plan**: Approve won't take the plan while ADR 51 is still Proposed. f286-02 (code lines in the review's numbers) can start as soon as it's queued. f286-01 starts after F280's ticket, which is 8th in the queue right now.
>    Action: Accept ADR 51, then approve the F286 plan.
>
> Proposals:
> - ADR 51: A review leaves the code simpler, and suggests the features that follow (adr)
> - F286: reviews look for complexity, suggest features, and show code growth (plan)
