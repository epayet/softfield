# F299: A card says when the factory suggested it, and who: a review, the lead, a page

The planning thread behind F299's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-25 08:25

> I want to be able to diffentiate whether a plant came from me, or from a suggestion from the factory, ie from a review

## The lead, 2026-11-25 08:30

> I've drafted a plan for F299: two tickets, a mock-up, and the card doc on `plan/f299`, with a few cards backfilled to the new form.
>
> 1. **Why you can't tell today**: Every plant goes through one runner step that always writes "Planted by the owner on …" on the card, whoever wrote the words. When you plant a review's idea, the dashboard already sends where it came from ("F286's review, idea 3"), but the runner ignores it. The only trace left is "From F286's review." glued to the end of the note. On the board, on the card's page and on its thread, the note is called "Your note". On top of that, reviews write their ideas in your voice on purpose. Ten cards carry a review or backlog origin today, among them F296, Show each milestone's net code lines, and F292, No terminal commands on the Overview.
>    Action: f299-01 makes the runner keep the origin it is already sent.
> 2. **Where the origin is kept: the card's header line**: The runner writes "Suggested by F286's review, planted by the owner on 25 Nov." in place of today's line, and one reader turns that line into a field the pages use. This works the same way as the fast lane mark. There's no new table or setting, and a merge keeps the kept card's header. A note from the Plant box keeps "Planted by the owner".
>    Action: D1 to D3 in the card doc; f299-01.
> 3. **Not only reviews: the lead and the Projects page too**: You said "from the factory, ie from a review". Two other sources plant words you didn't write. One is a seed the lead proposes on the general thread. The other is the Projects page's "Plant a card to fix it" and "Plant a card for a stack" buttons. I recommend marking all three: "F286's review", "the lead on the general thread", "the Projects page". A source the runner doesn't know plants as yours, never refused.
>    Action: D2; f299-01 adds the Projects page's source.
> 4. **What you see: a tag on suggestions only**: A suggested card gets a small dashed cog tag beside its key on the board ("F286 review"). On its page and thread, "Your note" becomes "F286's review suggested", with "you planted it on 25 Nov" and a link to that review. Your own cards don't change, so no tag means yours. I chose this over tagging both kinds: most cards are yours, and a tag on every card is noise. The tag is drawn in the ink colour, never a status colour. The picture is the mock-up, on real cards (F296 and F292 against F293, F297 and F298).
>    Action: Mock-up suggested-by.html; f299-02 builds it.
> 5. **The "From F286's review." tail goes, and old cards are fixed**: Once the header names the source, the tail at the end of the note says it twice, so the plate stops adding it. The plate finds its planted card by the source it sends, not by the words, so nothing breaks. The same ticket rewrites the ten cards on main: F258, F260, F269, F270, F271, F292, F295 and F296 get their review named in the header and their tail removed. F201 and F202 also get the new header naming the review behind them. F294, Sonnet takes Qwen's hard tickets, stays yours: you pasted the review's words into your own note yourself.
>    Action: D5; f299-01.
> 6. **Should reviews stop writing in your voice?**: That is part of why the cards blur. I recommend keeping it: the voice is there so an idea reads as something worth planting, and your notes stay comparable. With the tag, nothing is lost. The other choice is a neutral voice ("The board could show…"), which would make suggestions stand out even without a tag, at the cost of rewording the review's brief.
>    Action: Nothing, unless you prefer the neutral voice: then one line in the review's brief, added to f299-01.
> 7. **It shares a button with F297, Projects page plant buttons also ask the lead**: Both cards change what the Projects page's plant buttons send: F297 adds "ask the lead", this card adds "from the Projects page". They don't conflict. Whichever lands second keeps the other's part, and the card doc says so.
>    Action: Written in the Decisions; nothing for you.
> 8. **Who builds it, and how long**: f299-01 goes to the lead: it changes the runner and card docs, which are protected. f299-02 goes to a developer: it follows the mock-up and the existing "growing" tag, and waits for f299-01. Two tickets, about half an hour of work at today's pace. They join the line where you place the card on the board. Both pass pre-flight.
>    Action: Approve to queue both.
>
> Proposals:
> - F299: a card says who suggested it (plan)
> - F299 mock-up: a card says when the factory suggested it (mockup)

## The owner, 2026-11-25 20:56

> On point 6: does that mean you're thinking of figuring out where it came from by the text itself? the card should get some kind of metadata tag that has a few values, like origin: owner or origin:review, and also have whether i've tweaked it myself or not (i just planted a card about having the ability to tweak a suggestion before planting)

## The lead, 2026-11-25 21:37

> I've reworked the plan around the fields you asked for: an origin, which review, and whether you edited it. The card doc, both tickets and the mock-up are updated, and both tickets pass pre-flight.
>
> 1. **No: the origin never came from the words**: The first plan already took the origin from what the button sends, not from the note. I mentioned the "in your voice" style only because it's why the cards look alike to you today. But my first plan kept the origin as a sentence ("Suggested by F286's review, planted by…"), and you're right that fixed fields are better: a sentence is something the pages would have to parse.
>    Action: Replaced by point 2.
> 2. **Three fields on the card's header**: Each card's first line gets Origin, which is one of owner, review, lead or projects. A suggestion also gets From, the reviewed card (F286), and Edited, yes or no. Example: "State: idea · Area: factory · Origin: review · From: F286 · Edited: no". Your own new cards say "Origin: owner", and older cards without the field count as yours. The values come only from what the button sends, never from the text. "Planted by the owner on …" stays, as who pressed the button and when.
>    Action: D1 to D3 in the card doc; f299-01 writes and reads the fields.
> 3. **Edited needs F302, Edit a review's idea in its own plate before planting it**: This card adds the Edited field and the runner sets it when a plant says it was edited. Only F302's edit box can send that, when your words differ from the review's. So until F302 is built, a plant from a review's plate is always "Edited: no". That's true today, since the plate has no way to edit yet. I'm not merging the two cards: F302 is an edit box on the review plate, this card is the record and the tags. F302 goes after this card.
>    Action: The joint is written in the Decisions. F302's plan will send edited: true.
> 4. **Your hand-edited suggestions count as edited**: F294, Sonnet takes Qwen's hard tickets, and F303, A size limit for every Python file, are review suggestions you pasted into the Plant box and reworded. I traced them to F273's and F290's reviews. The backfill marks them "Origin: review, Edited: yes" with their notes untouched. It also covers F304, Backup tests use the shared fake clock, which arrived with the old tail since my last reply. That makes thirteen cards in all.
>    Action: Part of f299-01's one-off backfill.
> 5. **The mock-up now shows the fields and an edited card**: Proposed adds F296's header with the three fields, and F303 on the board tagged "F290 review · edited". The card page says "edited by you" when it applies. Cards with no tag are still yours.
>    Action: Mock-up suggested-by.html; f299-02 builds it.
>
> Proposals:
> - F299: a card says who suggested it (plan)
> - F299 mock-up: a card says when the factory suggested it (mockup)
