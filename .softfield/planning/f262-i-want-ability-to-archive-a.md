# F262: Archive a project: off the picker, its tickets wait, unarchive any time

The planning thread behind F262's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-17 19:48

> I want ability to archive a project so that only active projects are in the project picker. I might unarchive projects at any time and continue planning.
> Archived projects don't get their tickets picked up picked up from the board if there are any

## The lead, 2026-11-17 20:01

> I've drafted the plan for archiving projects, with a mock-up of the Projects page and the picker. Archive builds on F124, Pause one project from the Projects page, which hasn't been built yet. Archived means paused and taken off the lists.
>
> 1. **Archive builds on F124, Pause one project**: F124, Pause one project from the Projects page, is ready but not built. It already holds one project's tickets, checkpoints and reviews while that project's planning keeps answering. An archived project is held the same way, and it also leaves the project picker and the project list. So F262's tickets wait for f124-01 and f124-02, and the runner moves those two forward when F262's turn comes. Nothing else is built twice.
>    Action: Plan below; f262-01 waits for f124-01, f262-02 for f124-02
> 2. **Do you want Pause and Archive both?**: They overlap. Pause is for a short wait: the project stays in the picker and in the order. Archive is for a project you've put away: it leaves both. I recommend keeping both, with Archive as a quiet button at the bottom of the project's box, because you'll press it rarely, and Pause as the main button at the top. The other choices: (a) Archive only, with Pause working behind the scenes and no button of its own; (b) a single button that pauses and offers 'archive' once the project is paused.
>    Action: Keep both unless you choose (a) or (b)
> 3. **You can still plan an archived project**: You said you'd unarchive and then plan. I went one step further: while a project is archived, its Planning and Board pages still open from the Archived section, and if you write on one of its cards, the lead answers. Only its tickets wait. This costs nothing until you write. The alternative is read-only pages until you unarchive, which means extra code and one more button press for you.
>    Action: D2 in the plan
> 4. **What stays visible, so nothing is lost**: An archived project's cards, threads, tickets and order stay as they are. Anything of it that waits for you (a plan to approve) still shows under Needs you, because your words are never hidden. Its history stays in Runs, Jobs, Timeline and savings. It leaves the picker, the project list, the top bar's status and, once F132's floor has landed, the Overview's live view and the floor.
>    Action: D4; f262-03 is the extra ticket for the floor
> 5. **Unarchive brings it back running, at the bottom**: Unarchive sets the project running again, even if it was paused before you archived it. It comes back at the bottom of the project list (the order you send leaves archived projects out, so they drift to the end); drag it up if you want it higher. Archiving lets the job that's running finish, as Pause does, and you can't archive a project that is still being set up.
>    Action: D3, D5
> 6. **Forget stays as it is**: `softfield forget` in the terminal is still for a project whose folder is gone. F136, softfield init asks what to do with a forgotten project of the same name, relies on that, and a forgotten project can't come back from the dashboard. Archive is the dashboard's way to put a project away and bring it back. Merging the two would mean redoing F136.
>    Action: D6
> 7. **The mock-up: Projects page and picker**: Today versus Proposed, with real projects and counts from today. coaster-ranker is shown archived as an example (0 ready, 12 done): it's gone from the picker and sits in a folded 'Archived · 1' section under the list, with an Unarchive button in hazard yellow. coucou shows an archive on its way: a dashed orange 'Archiving…' button, as soon as you press it. F124's Pause is drawn plain because it lands first.
>    Action: .softfield/cards/f262-mockup/projects.html
> 8. **Three tickets, one lead and two developer**: f262-01 (lead, because the runner's code is protected): the archived state, the Archive and Unarchive requests, and holding the project's tickets. f262-02 (developer, following F124's Pause button): the picker, the top bar and the Projects page as in the mock-up. f262-03 (developer, an extra once F132's floor has landed): the Overview's live view and the floor leave archived projects out. That's about three hours of work, after F124's first two tickets.
>    Action: Drafts in .softfield/tasks/later/; all three pass pre-flight
>
> Proposals:
> - Archive a project: off the picker, its tickets wait (plan)
> - F262 mock-up: archive a project (mockup)
