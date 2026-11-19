# F273: Forget a project from the Projects page

The planning thread behind F273's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-19 12:12

> I need the ability to forget a project from the web projects page

## The lead, 2026-11-19 12:18

> I drafted the plan, a mock-up and two tickets on top of F262's Archive. The one choice I'm asking you to make is where Forget goes.
>
> 1. **This reverses a decision in F262, Archive a project**: F262 is ready and its tickets are queued. Its D6 kept Forget in the terminal only, with Archive as the dashboard's undoable option. Now that you can start projects from the Projects page (waifu-gallery is the first), it makes sense to remove one there too. So F273 isn't a repeat of F262: it builds on it. Its tickets wait for F262's, and F262 stays as it is.
>    Action: Plan F273 on top of F262; f273-01 waits for f262-01, f273-02 for f262-02.
> 2. **Forget only from the Archived section, not from every project**: I recommend that Forget appears only on archived projects: you archive first, then forget. A wrong tap on a running project can't take it off every page, and an archived project's tickets are already on hold, so nothing is mid-ticket when the forget lands. The cost is one extra press for a project you're sure about. The other option is a Forget button on every project, with the same confirmation question. That's one step shorter, but it's a fourth button next to Pause, Archive and the app controls.
>    Action: D2 as drafted, unless you'd rather have Forget on every project.
> 3. **Forget deletes nothing**: Forgetting from the web does exactly what `softfield forget` does: the project leaves every page and the runner, and its cards, threads, history and folder all stay. To bring it back, run `softfield init` in its folder and choose Continue (F136, softfield init asks what to do with a forgotten project of the same name). Deleting the data stays a terminal-only step: init's "start fresh". The confirmation question says all this, and how many open items for you go with the project.
>    Action: D1, D4 and D6 in the card doc.
> 4. **Not while its app is running**: waifu-gallery's app is running on :8120 right now. If you forgot it as it is, the app would keep running with no page left to stop it from. So an archived project whose app runs shows its app controls (Stop, Logs) in the Archived section, and Forget stays greyed out until you stop the app. The runner refuses the forget too, as a backstop.
>    Action: D3, in both tickets.
> 5. **The mock-up**: `.softfield/cards/f273-mockup/projects.html` shows the Projects page today, and after F262 and F273. On the after side, press Forget on coaster-ranker: a striped question opens under it (no pop-up), and "Yes, forget it" turns the button orange and dashed: "Forgetting…, on its way". waifu-gallery shows the case where the app is still running. I didn't add a list of forgotten projects to bring one back from the page: init already does that. It can be a later card if you want it.
>    Action: f273-02 builds the mock-up's after side.
> 6. **Two tickets, small**: f273-01 (mine, since the runner's code is protected): the forget request, its two refusals, and the runner's wording. f273-02 (a developer's): the Forget button, the question and the app controls in the Archived section, following F262's Unarchive button. Both pass pre-flight. They run once F262's tickets have landed.
>    Action: Queue both on approval.
>
> Proposals:
> - F273: forget an archived project from the Projects page (plan)
> - Projects page: Forget in the Archived section (mockup)
