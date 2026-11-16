# F201: Ticket pages, card notes and lead replies render code, bold and links

The planning thread behind F201's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-14 12:40

> Plan this card.

## The lead, 2026-11-16 19:27

> I've planned F201 on top of F216, A shorter, consistent review page, which is already building the markdown rules F201 was waiting for. The plan is two tickets, a mock-up and the card's doc; both tickets pass the ticket check.
>
> 1. **The renderer this card waited for is already planned**: F216, A shorter, consistent review page, has ticket f216-02 teach `_to_html` backticks, bold anywhere and http(s) links, for the review sheet. F201 doesn't build a second renderer. It reuses those rules, so it waits for f216-02, and for f216-03 because that ticket rewrites the card page's template.
>    Action: f201-01 depends on f216-02 and f216-03
> 2. **Where it applies: the ticket page, the card's note, and the lead's replies on a thread**: The card's note covered the ticket page and card docs. I added the lead's replies on a thread, because that's where you read the most backticks today (for example ticket names in my points). The structure stays as it is: the ticket page keeps its paragraphs and lists, and a note keeps its line breaks. Only the text inside them is rendered. Your own messages on a thread stay plain, as they are now.
>    Action: 01 covers the ticket page and the notes; 02 covers the lead's replies. Say if you'd rather drop 02.
> 3. **Mock-up: only the text changes**: The mock-up shows f216-02's Goal panel and F201's own note, with their real text, as Today and Proposed. Backticks become the dashboard's existing code chip and stars become bold. No panel, colour or token changes.
>    Action: Mock-up .softfield/cards/f201-mockup/ticket-and-note.html; 01 names it as the picture to build
> 4. **Typed HTML still shows as typed**: Text is escaped before any markdown is applied. Links are made only for http:// and https:// addresses; anything else, javascript: included, stays as plain text. On a thread, markdown links are left out, so a card or ticket reference can't land inside a link's address and break the page. Both tickets test this first.
>    Action: Covered in each ticket's Done when
> 5. **Who builds what**: 01 goes to a developer: it splits one function, adds one template filter and makes one-line template edits, and `_to_html`'s existing tests show how. I take 02 myself: it runs substitutions on escaped HTML in front of the reference links that every thread uses, so a slip breaks every thread.
>    Action: 01 developer (difficulty 3), 02 lead (difficulty 3)
>
> Proposals:
> - F201: ticket pages, card notes and lead replies render code, bold and links (plan)
> - F201 mock-up: ticket and card pages render their markdown (mockup)
