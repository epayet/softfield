# F68: I want the factory to be renamed SoftField. That should be…

The planning thread behind F68's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 08:41

> I want the factory to be renamed SoftField. That should be visible top left, let's talk through designs of a fun relevant logo too. also the top left text + logo should bring back to overview when clicked

## The lead, 2026-10-09 08:46

> I've drafted the SoftField plan on `plan/f68`: four logo designs in a mock-up you can switch between light and dark, the updated card doc, and one developer ticket. Nothing is queued until you approve it.
>
> 1. **The logo: four designs, A recommended**: SoftField works as "a field where software grows", and the dashboard already talks that way: you plant ideas and the floor has a Planting lane. Each design joins the field's green to the factory's hazard yellow. A: a sprout growing out of one of the floor's crates. B: a field's furrows drawn as indented lines of code. C: a sprout whose flower is a cog. D: the hazard stripe as a sun rising over furrows. I recommend A. It ties planting to the factory most plainly and is the only one that still reads at 16 px, the size of the browser tab's icon. B looks like a menu icon at that size, and C's and D's details blur. D is the prettiest large, if you'd rather have that.
>    Action: Pick A, B, C or D in docs/milestones/f68-mockup/logos.html. The ticket is written for A, and I'll switch it if you pick another.
> 2. **The name and the logo go back to the Overview**: The logo and the name become one link to the Overview. It keeps the project you have chosen, as the Overview tab does, and is at least 44 px tall so it's easy to tap on a phone.
>    Action: Ticket f68-01
> 3. **Written "SoftField", not "SOFTFIELD"**: Today the top bar shows its name in capitals, which would turn SoftField into SOFTFIELD and lose the capital F where the two words meet. I suggest normal case, with "Soft" in the text colour and "Field" in the sprout's green. The mock-up shows both versions side by side.
>    Action: Ticket f68-01 (D2)
> 4. **Rename only what you see, not the folders behind it**: The visible name changes everywhere: the top bar, the page titles, the browser tab's icon (there's none today) and the app's own title. The metrics database folder, the Dropbox backup folder, the benchmark cache and the `runner` commands keep "software-factory". Renaming those would move your data and backups for nothing you'd see, and a slip there is how a backup gets lost. If you want SoftField to be the name of the separate repo and its command, that belongs to ADR 02's split of the factory into its own repo.
>    Action: Milestone decision D1. If you want the repo named SoftField, I'll add it to ADR 02's open questions.
> 5. **Waits for F17, which rebuilds the same row**: Ticket f17-01 (ready) rebuilds the top bar's phone row: the dot and the pause sign go beside the name. Ticket f9-30 (ready) tests where the name sits in that row. f68-01 depends on both, so it isn't redone. SoftField is also shorter than software-factory, which helps that row fit on a phone; the ticket checks that it still fits at 390 px.
>    Action: depends_on in f68-01 (D4)
> 6. **Works with the night switch (F69)**: The logo takes its colours from the dashboard's own colour settings, so it changes with the light and dark themes and with F69's switch once that exists. F69 is a separate request, not a repeat of this one. The mock-up has a button to check each design in both themes.
>    Action: Nothing: F69 stays its own card
> 7. **The name may already be taken**: "SoftField" is fine for a dashboard on your home Wi-Fi. If ADR 02 later publishes the factory, someone else may already use the name; I haven't checked. For coucou, docs/brand/name-check.md did that kind of check.
>    Action: Roadmap: check the name before ADR 02 publishes anything
>
> Proposals:
> - SoftField: four logos in the top bar (mockup)
> - F68: SoftField, its logo and a link home (plan)

## The owner, 2026-10-09 09:27

> I sent back your proposal “SoftField: four logos in the top bar” (f68-mockup).
> - On its key point 3 (The name in two looks): what if Soft is yellow. Field stays green, how would that be? update mockup and compare

## The lead, 2026-10-09 09:31

> I added a yellow-and-green version of the name to the mock-up, next to the other two looks, each shown on the dark and the light background. I recommend it, and the plan and ticket now use it.
>
> 1. **Yellow "Soft", green "Field": I'd take it**: It's better than my ink-and-green version. The name now repeats logo A's two colours, the yellow crate and the green sprout, so the logo and the name read as one piece. On the dark background it's lively and easy to read. The mock-up's "The name" section now shows three looks, each on the dark and the light background, so you can compare them directly.
>    Action: Plan D2 and ticket f68-01 now use yellow and green
> 2. **On the light theme the yellow has to be darker**: The hazard yellow is unreadable on the light background: about 1.8 to 1 contrast, where text needs 4.5 to 1. In the light theme, "Soft" turns a deeper amber, the colour the light theme already uses for yellow words. The mock-up shows the pale yellow next to it so you can see the problem. When F69's switch comes, the name changes colour with it.
>    Action: Ticket f68-01 colours "Soft" with the dashboard's existing yellow-for-text colour, which handles both themes. A browser test checks the light theme.
> 3. **A small risk: yellow already means things in the bar**: The current tab is a yellow block, and yellow words elsewhere mean "past the mark". A yellow word at the top left could look like one of those. I think the logo beside it makes it clearly the name, so I wouldn't change anything, but look at it on your phone.
>    Action: Nothing, unless it looks wrong on your phone
>
> Proposals:
> - SoftField: four logos in the top bar (mockup)
> - F68: SoftField, its logo and a link home (plan)
