# F236: softfield init adds the project only when its setup ends and doctor passes

The planning thread behind F236's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-09 17:16

> Softfield init adds a project to the list as soon as Claude starts before even I prompted anything, it should do it at the Claude session exit instead only once there is an actual plan and doctor is all good. Claude should also tell me if not already when I'm ready to leave the session and they the project will be created

## The lead, 2026-11-09 21:05

> I drafted a plan with two lead tickets: the project joins the factory only when you leave the setup session with `doctor` passing, and Claude tells you when you can leave. Both tickets pass the ticket check.
>
> 1. **Why the project shows before you've said anything**: `softfield init` registers the project as "setting up" before it hands the terminal to Claude, and the Projects page lists it from then on. `doctor`, run at the end of the session, only lifts that pause. I agree with your change: a setup you give up halfway would otherwise leave a row on the list.
>    Action: The plan below: only a passing `doctor` registers the project.
> 2. **A trap: accepting ADR 00 would add the project too**: `softfield accept 0`, which Claude runs on your yes, creates the project's row if there isn't one, and that row isn't paused. If init stopped registering and nothing else changed, accepting ADR 00 would put a half-set-up project on the runner's line, which is worse than today.
>    Action: Ticket f236-01 makes accept (and reject) write only to a project that is already registered.
> 3. **Claude says when you can leave**: Inside the setup session `doctor` only checks. When everything passes it prints "Ready: leave this session (/exit) and <name> joins the factory", and Claude's last message repeats it. When you exit, init runs `doctor` once more with the full checks. If it passes, the project is added and you get the dashboard links. If it doesn't, you get what's left, "Nothing was added to the factory", and running `softfield init` again in that folder carries on the setup with Claude.
>    Action: Ticket f236-02 (init waits for Claude, the setup guide's last step, and init carrying on).
> 4. **The hidden cost: a setup you leave has no reminder**: If you leave before `doctor` passes, the folder keeps its files and commits, but nothing on the dashboard shows it is waiting. The last thing the terminal says is how to carry on, and that's all you get. I think that's right for a project that was never finished, but you lose the "Being set up on its computer" line on the Projects page.
>    Action: None, unless you want an item on the desk for a setup left unfinished.
> 5. **Built after F136, softfield init asks what to do with a forgotten project of the same name**: Two of F136's ready tickets (f136-02 and f136-03) rewrite the same code in `init`. F236 waits for them and builds on what they leave. Their question about the old project is still asked when init starts, but the new project is registered, or the old one brought back from forgotten, only when `doctor` passes.
>    Action: f236-01 depends on f136-03.
> 6. **This changes something ADR 30 decided**: ADR 30, Many projects, one factory (item 7) says init registers the project. Your approval of this plan is the decision, and f236-01 adds a dated line to ADR 30 saying F236 changed it. I don't think a new ADR is needed for this.
>    Action: As part of f236-01.
> 7. **No mock-up**: Everything changes in the terminal. The Projects page only stops showing a project before its setup is done, and nothing new is drawn on it.
>    Action: None.
>
> Proposals:
> - F236: the project joins the factory when its setup ends (plan)

## The owner, 2026-11-09 23:05

> Is my coaster ranker ready to go? It's not being worked on Claude said it was fine
>
> On point 1: Doctor doesn't sound like it will finish the init step, Claude should just tell me and ask me or something or maybe a softfield create after init which will run doctor before the final creation. Claude could suggest or run it for me

## The lead, 2026-11-09 23:08

> Coaster-ranker isn't ready to go. The setup handed it over correctly at 21:34, but the runner has never started it. I revised the F236 plan to use your `softfield create` and added a ticket so a project the runner can't start shows on your desk.
>
> 1. **Coaster-ranker: handed over, but the runner can't start it**: The setup itself went fine. ADR 00 was accepted, `doctor` passed at 21:34 and coaster-ranker is #1 on the Projects page with its first card, M1 'Import our two lists and rank the Orlando coasters by dragging'. But the runner has never started a session for it (there's no run in the database). So the lead's 'Plan this card' job has been waiting since 22:38, while softfield jobs queued after it went first. The runner skips a project when its folder isn't on main or has changes that aren't committed. It says so only once, in its own terminal window, which is why the Projects page shows 'nothing for you'. The folder is on main, so uncommitted changes are the likely cause. I can't run git in another project's folder from here to name the files.
>    Action: On the computer, open the coaster-ranker folder, see what git lists as changed and commit it, or ask Claude there to do it. The runner's terminal window also shows the exact reason. At its next round the runner picks the project up and the lead plans M1 on its thread. Nothing gets built until you approve that plan.
> 2. **So this doesn't happen silently again**: When the runner can't start a project, it will put an item on that project's Planning desk with the reason: the branch it's on, or up to ten files that aren't committed. The item clears by itself at the first round the project starts. It uses the desk's existing look and the Projects page's existing 'for you' count, so there's no mock-up. It doesn't wait for F136 (softfield init asks what to do with a forgotten project of the same name), so it can run early.
>    Action: Ticket f236-03-a-project-that-cant-start-says-why.
> 3. **Your `softfield create`: agreed, and doctor goes back to only checking**: You're right that 'doctor' doesn't sound like it finishes anything. The plan now works like this. `doctor` only checks, and when everything passes its last line says that `softfield create` adds the project. `softfield create` runs the same checks and, if they pass, adds the project to the factory and prints the dashboard links. It replaces my 'register on exit' and the hidden setup switch I had planned for the session, so the plan is simpler. Claude runs `doctor`, fixes what it says, asks 'Ready to add coaster-ranker to the factory?', and on your yes runs `softfield create` itself. It ends with 'You can leave this session now (/exit)'. Claude never runs `create` without your yes.
>    Action: Ticket f236-01 (`create`, `doctor` only checks, accept no longer adds the project) and ticket f236-02 (Claude asks, then runs it).
> 4. **Leaving the session early**: If you leave before the project is added, `init` says '<name> isn't in the factory yet', and that running `softfield init` again in that folder carries on with Claude, or `softfield create` adds it if it's ready. It doesn't add the project on its own when you exit. Creating it is always your yes, so nothing gets added by surprise.
>    Action: Part of f236-02.
> 5. **A ticket keeps its old name**: f236-01 is still called 'doctor-registers-the-project', because this job can't rename files. Its goal says plainly that it builds `softfield create`.
>    Action: None.
>
> Proposals:
> - F236: `softfield create` adds the project, on your yes (plan)
