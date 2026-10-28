# F136: softfield init asks what to do with a forgotten project of the same name

The planning thread behind F136's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 04:36

> I've planned F136 as three tickets for the lead, since everything is in the protected `runner/`. I read the cause in the database and the code, and the points below cover it.
>
> 1. **Why archiving took both M1 cards**: `softfield forget` only marks the project as forgotten. Its cards, tickets and threads stay in the database under the same entry. Running `init` again under the same name quietly takes that old entry back. Your test-factory-hello holds both lives today: the old card M1 'hello and happy birthday' (its file went with the old folder) and the new M1 'uv run hi'. Two things share only the short key `m1`: the board's clean-up of cards whose file is gone, and the card's thread. So the new M1 kept the old one on the board, both hung off one `m1` thread, and archiving that thread archived both.
>    Action: f136-01 and f136-02 fix both halves.
> 2. **Continue: only when the folder still holds the old project**: I'd narrow your first choice. Continuing the old history in a fresh folder is exactly what broke your test: the new cards start again at M1 and land on the old M1's thread. So 'continue' is offered only when you run `init` in the old project's own folder (its files still there). It then brings the project back without writing anything. In a fresh folder you choose between keeping the old entry and starting fresh.
>    Action: Ticket f136-02 (D2 in the card).
> 3. **Keep both: the old one becomes hello-1, not the new one**: Your 'make a new entry (like -1)' works best the other way round. The old entry is renamed hello-1 and stays forgotten, with all its history. The new project keeps the folder's name, which its settings file, the dashboard's address and the hand-over all use. This is the default choice.
>    Action: Ticket f136-02.
> 4. **Start fresh deletes the old costs too: is that fine?**: Wiping the old entry deletes its cards, tickets, threads, and its runs with their costs, so its share of the savings on the Overview goes with it. The agents' ratings stay, and so does the daily Dropbox backup until it rolls over. To guard against a slip, you type the project's name back before anything goes. My recommendation: yes, as described. Alternatives: (a) keep the old runs and costs under a hidden name and delete only cards, tickets and threads; (b) no 'start fresh' at all, only keep.
>    Action: Ticket f136-03 as written, unless you pick (a) or (b).
> 5. **A worse clash you didn't hit: two live projects with one name**: Today `init` in a second folder called `hello`, while another `hello` is still running, takes over that live project and points it at the new folder. With this plan the live one is never touched: the new project is named hello-2 in its own settings.
>    Action: Ticket f136-02.
> 6. **The board drops a gone card even when a new one shares its number**: Separately from `init`, the runner's card clean-up will remove a card whose file is gone even if another card file has the same short key. So two cards can never share one thread again, whatever caused the overlap. Card files are never renamed (naming a card rewrites only its heading), so this is safe.
>    Action: Ticket f136-01 (D5).
> 7. **No mock-up**: Everything here happens in the terminal: the question `init` asks, and a database clean-up. No dashboard page changes.
>    Action: Nothing.
> 8. **Another card's draft fails the ticket check**: The check on drafts found a problem outside F136. F9's draft f9-12-fix-the-desktop-test-does lists only test files, so it can't pass the 'tests fail on main' gate as a developer ticket.
>    Action: When F9 is replanned, mark it `tests_only: true` or give it to the lead. Nothing to do on this card.
>
> Proposals:
> - F136: init asks what to do with a forgotten project's old data (plan)
