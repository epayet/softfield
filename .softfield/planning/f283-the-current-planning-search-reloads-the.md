# F283: Light up matching cards on the board as you type; the rest stay in place

The planning thread behind F283's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-21 05:04

> The current planning search reloads the whole page and I assume is doing a search not just on the ticket name but also the description etc. It really filters out every other ticket I sometimes use this when I'm searching a ticket by number. Having said that if it was doing some kind of fuzzy search whenever a ticket number was mentioned other tickets would have popped up as well.
>
> The annoying thing is that once I found what I want I can't compare the filtered out tickets compared to the rest.
> The main use case that I think is missing is having the ability to highlight my search while still seeing the other tickets so that I may decide to bring the one I'm looking for higher.
>
> So I think filtering out everything and doing fuzzy search is one use case, which I use less. This reloads the page
>
> What I'm looking for is a bit like the developer view. If I type a few words, every ticket not related stays where they are but are greyed out and the ones with the words I typed stay colored or even highlighted so that I can see them and drag them in other places easily. Not sure how to call this text box, highlight rather than filter? This one would be dynamic using JavaScript and the text available on screen (titles)

## The lead, 2026-11-23 22:23

> I've drawn the mock-up and drafted the plan for the board's Find box: two developer tickets, both passing the ticket check.
>
> 1. **What the search does today**: The box you mean is the Board's search (`/board`), not the Planning room's. It reloads the page and keeps only the cards whose number or title holds what you typed, as one piece of text. It never searches a card's notes or tickets. A number is matched as text inside the number, so `f28` already keeps F28 and F280 to F286 too. That's why a search by number sometimes brings others.
>    Action: Nothing. It's what the plan builds on.
> 2. **One box, not two**: You asked whether to have a Highlight box and a Filter box. I'd push back on two boxes: on a phone, two text boxes take up the space above the cards, and you'd have to pick one before typing. Instead, one box labelled **Find**. Typing, or pressing Enter, lights up cards at once with no reload. A button beside it, **Show only these**, does today's filter with its reload, for the less common case.
>    Action: Decision D1 in the card's doc; built by ticket f283-01.
> 3. **What lights up**: Only what each card shows: its number and its title. Every word you type has to be there, in any order, so "top bar" finds "the top bar's dot" too. A card number is matched whole: `f38` or `38` lights F38 and never F380. That covers your search by number without the extra hits. Any other word, `bug-41` included, can be anywhere in the number or the title. Harvested only shows its latest 4 cards, so older ones can't light up. Show only these still finds them.
>    Action: Decision D2; ticket f283-01.
> 4. **How it looks: faded, lit, and still draggable**: Cards that don't match stay where they are and fade, as in the developer's view, and come back when the pointer is on them. Lit cards get a new colour, a cold white "searchlight" (`--lit`), as their edge and glow, with a small `lit` tag and the matching words marked. It's not a status colour and not an agent's colour. Every card keeps its grip, so you can drag F256 from #74 up past F37 and see what it jumps over. The light stays on through a drag, moves not yet sent, the developer's view and the 10-second refresh. Reloading the page or pressing Esc clears it.
>    Action: Decisions D3 and D4; ticket f283-01. Try typing in the mock-up's Proposed box: it works.
> 5. **Finding the lit card in a long column**: Planted holds 75 cards, so a lit card at #74 is off screen. Beside the box: "6 lit" and a **Next ›** button that scrolls to each lit card in turn. On a phone, where only one stage shows at a time, each stage button at the top says how many of its cards are lit, and Next › switches to the right stage.
>    Action: Ticket f283-02.
> 6. **Who builds it, and when**: Two small developer tickets, in the board's own script, template and styles, following the developer's-view fading and the existing browser tests. f283-01 waits for f123-01 (F123, Projects page: drag projects into order, as on the board), which moves the board's drag code into a shared script, so the two don't clash. At about 46 minutes per ticket, that's around 1.5 hours of work once its turn comes.
>    Action: Plan below; nothing is queued until you approve it.
>
> Proposals:
> - The board's Find box: Today (filtered) and Proposed (lit in place) (mockup)
> - F283: light up matching cards on the board as you type (plan)
