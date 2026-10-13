# F109: Merged cards link to each other, both ways

The planning thread behind F109's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-13 04:16

> When plans get merged, I need to be able to go from one to the other (I have no links ATM)

## The lead, 2026-10-13 04:22

> Both tickets pass pre-flight. The plan for this card is drafted on `plan/f109` and waits for your Approve.
>
> 1. **Why you have no links today**: When a card is merged, the merged card's thread gets one line from the lead ending in "/planning/f95", but the page shows it as plain text, not a link. The kept card's thread gets nothing at all. The merged card's page also shows its bare key ("f107") as its title, because its card has left the board.
>    Action: One developer ticket, f109-01-merge-links: the links go in the thread page's header, both ways.
> 2. **What you will see**: On the merged card's thread: "Merged into F95, <its title>" under the title, as a link, and the card's own title instead of its key. On the kept card's thread: "Merged here: F107, <its title>", one link per merged card, with the date. The path in the lead's line becomes a link too. All of it is in the header, so it is above the fold on a phone.
>    Action: Part of f109-01-merge-links. No mock-up: it is two lines of links in a header that exists.
> 3. **The 19 merges already done get their links too**: Every merge already writes a heading in the kept card's notes ("From F107: … (merged by the lead on 2026-10-13)"). The dashboard reads the links from those headings instead of storing them, so nothing changes in the runner and old merges work at once. I turned down a new database column: it would need a protected lead ticket, a migration and a backfill for the same result.
>    Action: Decision D2 in the card's doc; nothing for you to do.
> 4. **A problem I found: a merged card's key is given to the next plant**: When the highest-numbered card is merged away, the next idea you plant takes its number. F64 was planted and merged three times (into F13, Planting idea UI feedback; F42, The space for me to scroll; and F9, Line polish). F73 and F107 were used twice. So /planning/f64 holds three different conversations, and a link "back to F64" can't say which one.
>    Action: One small lead ticket, f109-02-keys-not-reused: a key that has a thread is never planted again. It has no dependency, so it can run beside the developer ticket.
> 5. **The threads already mixed stay mixed**: For F64, F73 and F107 the page will list every card the key was merged into, with dates. Where the key has a card again (F73, I want to be able to, is an idea today), it says "An earlier F73 was merged into F43". Splitting those old threads apart would need a migration of the planning data, which I don't think three threads are worth.
>    Action: Nothing, unless you want them split: say so and I'll add a ticket.
> 6. **Not a repeat of F49, Don't ask me to merge conversations**: F49's waiting ticket (f49-02-merge-context) adds a line on the kept thread, "Merged F44 here: <summary>", but as plain text with no link. This card adds the links and leaves that ticket alone: the header links back whether or not it has run.
>    Action: Nothing.
> 7. **The card's own page is left for later**: The same links would be useful on the card's page, but F5, the board, is building that page now (f5-17-card-page) and I shouldn't plan on top of a page that isn't on main.
>    Action: Noted under "Later" in this card's doc; a ticket once the card page has merged.
>
> Proposals:
> - F109 plan: 2 tickets (plan)
