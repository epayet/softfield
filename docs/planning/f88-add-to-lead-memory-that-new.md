# F88: add to lead memory that new software factory features…

The planning thread behind F88's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 20:34

> add to lead memory that new software factory features should be done with the main theme. the inspiration source is arknight endfield factory system, the colors are inspired from that. it should be subtle though and not copyright issue so be careful. but all new features should be designed with that in mind rather than bland. i can tone down if necessary in proposals/mock ups, rather than tone up to be more fun

## The lead, 2026-10-09 20:44

> I've drafted F88 as one small lead ticket. The theme rule goes into the lead's preferences (`owner.md`), `lead.md` and the planner's brief. Below are the points where I push back on how it's worded.
>
> 1. **What you get**: Every new factory page, element and mock-up starts in the factory theme, a bit bolder than needed, so you tone it down rather than ask for more fun. The rule goes in three places. Your preferences file (owner.md) is pasted into every lead job. lead.md is for terminal sessions. The planner's mock-up instructions make sure a mock-up's Proposed side always comes themed. The ticket itself is lead work, but it can't be a single line in a memory file: every ticket needs a test that fails without the change, so this one checks the planner's instructions.
>    Action: Ticket f88-01-factory-theme-rule (lead, difficulty 2)
> 2. **"Endfield" alone is too vague a brief**: Many of the agents (the local developer models, a fresh headless job) don't know the game. Also, telling an agent to look like a named game invites copying, which is the exact risk you raised. So the rule describes the look in concrete traits we already have in dashboard.css: a dark industrial floor with bays and plates, hazard yellow and stripes, angular Chakra Petch headings, mono labels, thin rules and a faint grid, corner ticks, equipment-plate panel headers, machines, belts and crates. The game is named once in owner.md, as where the mood comes from. Any new colour or shape is added to the dashboard's shared colour and style settings before a page uses it.
>    Action: D1 in the ticket
> 3. **The copyright guard**: Nothing is taken from the game: no names, logos, characters, icons, screenshots, sounds, game fonts or traced layouts. The word never appears on a page or in an asset, and every drawing is our own SVG or CSS. Our three fonts (Chakra Petch, Barlow, JetBrains Mono) are under an open licence, so they're safe. The planner's instructions won't name the game at all, and a test makes sure of that.
>    Action: D2 in the ticket
> 4. **Decoration vs your rule that every mark must mean something**: You asked on 2026-10-02 that every colour, bar or light say what it means, or go. Theme decoration (corner ticks, stripes, a grid) is a mark that means nothing. So I'd add a carve-out: decoration is allowed, but it only uses the plain ink, the rule lines and the hazard stripe. It never uses a colour that carries meaning (an agent's colour, fail, warn, good), and it never blinks or shows a number. That way nobody mistakes a decorative stripe for a warning.
>    Action: D3 in the ticket, and a change to your 2026-10-02 rule
> 5. **Mum's product keeps its calm look**: The theme applies to the factory only. Coucou stays calm and ambient, as your product taste says. Product work is on hold anyway.
>    Action: D5 in the ticket
> 6. **F81 is related, not a repeat**: F81, planted the same day, asks me to assess today's pages and suggest bolder, Endfield-inspired changes: a one-off pass over what already exists. F88 is the standing rule for new work. Keep both. F81's proposals will follow this rule.
>    Action: Nothing; a note under Later in F88's doc
> 7. **It waits for f72-01**: f72-01 (mock-ups by default, already ready) edits the same three files and adds the mock-up paragraph this ticket extends, so f88-01 depends on it. Nothing in the ready queue changes, so you don't need to pause the factory.
>    Action: depends_on: f72-01-mockup-by-default
>
> Proposals:
> - F88: new factory features in the factory theme (plan)
