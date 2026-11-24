# Milestone F283: Light up matching cards on the board as you type; the rest stay in place

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-21.

## Notes
The current planning search reloads the whole page and I assume is doing a search not just on the ticket name but also the description etc. It really filters out every other ticket I sometimes use this when I'm searching a ticket by number. Having said that if it was doing some kind of fuzzy search whenever a ticket number was mentioned other tickets would have popped up as well. 

The annoying thing is that once I found what I want I can't compare the filtered out tickets compared to the rest. 
The main use case that I think is missing is having the ability to highlight my search while still seeing the other tickets so that I may decide to bring the one I'm looking for higher. 

So I think filtering out everything and doing fuzzy search is one use case, which I use less. This reloads the page 

What I'm looking for is a bit like the developer view. If I type a few words, every ticket not related stays where they are but are greyed out and the ones with the words I typed stay colored or even highlighted so that I can see them and drag them in other places easily. Not sure how to call this text box, highlight rather than filter? This one would be dynamic using JavaScript and the text available on screen (titles)

## What is there today
The box is the board's search (`/board`, `factory_dashboard/templates/board.html`, the `board-filter` form). It is a plain GET form: Enter reloads the page with `?q=`, and `_matches` in `factory_dashboard/board.py` keeps the cards whose key or title holds the text, as one piece (`"top bar"` must appear as is). It never reads a card's notes or tickets. A number is a substring too: `f28` keeps F28 and F280 to F286.

## Decisions
The picture to build: `.softfield/cards/f283-mockup/board-highlight.html` (Proposed).
- **D1 One box, two ways.** The box is labelled **Find**. Typing lights up cards at once, in the browser, with no request; Enter does the same and never reloads. A button beside it, **Show only these**, sends today's form (`?q=`, the reload, the server's `_matches` unchanged). Without the script the form works as today. The `kind` buttons and the developer's view lever stay as they are.
- **D2 What lights up.** Only what the card shows: its key and its title, as drawn on the page (`.card-meta` key, `.card-title`). The text is split into words; a card lights up when every word is in it, in any order, case aside. A word that is a card number, `f` and digits or digits alone (`f38`, `38`), matches a card's key whole (`F38`, never `F380`, never a title); any other word, `bug-41` included, is found anywhere in the key or the title. Harvested shows its latest cards only, so older ones can't light up: "Show only these" still finds them.
- **D3 How it looks.** Cards that don't match stay in their place, at opacity .28, and come back to .85 under the pointer or the focus (as the developer's view's faded cards do). A lit card gets a new token, `--lit` (a cold white, `#e6f4ff`; in the light theme a dark ink, `#1b2633`), as a 2 px edge and a soft glow, a small `lit` tag, and its matching words wrapped in `<mark>`. Not a status colour, not an agent's. Beside the box: "N lit" and a **Next ›** button that scrolls the next lit card to the middle of the screen, in the page's order, round again after the last. Each plot gets an "N lit" tag while the box holds text, since a phone shows one stage at a time.
- **D4 It stays on.** The light survives a drag, moves not sent, the ⋯ menu, the developer's view (the light decides the fading while the box holds text; the developer tags stay) and the 10 s refresh (applied again after `.stages` is swapped). It isn't in the address: a reload of the page starts dark. Esc or the box's × clears it.

## Tickets
- f283-01-find-lights-up (developer): D1, D2, D3's fading, edge, tag and marks, D4.
- f283-02-lit-count-and-next (developer): D3's "N lit", Next › and the plots' tags.

## Before and after
- `/board`
