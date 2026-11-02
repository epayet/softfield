# F178: Backups on the dashboard: copies, size, last copy, and a desk item on failure

The planning thread behind F178's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-29 18:56

> Plan this card.

## The lead, 2026-10-29 20:22

> I've drafted the plan for F178, a mock-up and three tickets on `plan/f178`, and pre-flight passed all three tickets. F178 isn't a repeat of F131: it came out of the answer on that thread.
>
> 1. **Nothing shows the backups today**: The runner copies the metrics database to ~/Dropbox/software-factory-backups once a day and keeps the last 14. Today the folder holds 14 copies, from 9 Oct to 28 Oct 23:05. When a copy fails, all you get is a line in the console and one note in the session report, so it can go unnoticed for days. This card came out of my answer on F131, How many metrics backups the Dropbox folder keeps.
>    Action: The plan below.
> 2. **A Backups section on the Projects page, not on the Overview**: The copies belong to the machine, not to one project, and the Projects page is the one above every project. So the new section goes there, under Projects. It shows how many copies are kept out of 14, their total size and the average, when the last was taken and how long ago, and when the next is due. Below that is a shelf with one crate per copy, oldest on the left; tap a crate for its date and size. The mock-up has three states: all well, failing for an hour, and the runner was off. The sizes in it are examples: I can list the files from here but not measure them.
>    Action: Mock-up f178-mockup/backups.html; ticket f178-02.
> 3. **Desk item after an hour of failures, not the first one**: Your note asks for a desk item when a copy fails. I'd wait until copies have failed for an hour. A single failure is often Dropbox holding a file for a moment, and the retry 5 minutes later works. An item for that would show up and vanish, which is noise. After an hour of failures, an item goes on the Planning desk of the project being run, first on the desk in red, with the error. It clears by itself once a copy works, so there's no button. It also shows in the Overview's Needs you, like any desk item.
>    Action: Tickets f178-01 (the runner opens and clears the item) and f178-03 (the desk group).
> 4. **One phone notification when the item opens**: A broken backup is the kind of thing you'd want to hear about while you're away, so the runner sends one notification when the item opens. Further failures update the item's text and don't send again. Say so if you'd rather it stayed silent.
>    Action: Part of f178-01.
> 5. **No copy while the runner is off is not a failure**: Only a running runner takes copies. After a few days off, the section says calmly 'No copy for 3 days', with no red and no desk item. The next copy is taken as soon as the runner starts.
>    Action: Part of f178-02.
> 6. **Who builds what**: The runner side is the lead's work, because runner/ is protected. That covers reading your backup settings, the list of copies with their sizes, and the desk item with its notification. The page section and the desk group are two small developer tickets that follow existing code: the Projects page, and the desk's blocked-tickets group. Both wait for f178-01.
>    Action: f178-01 (lead), f178-02 and f178-03 (developer), about 3 tickets of roughly 50 minutes each.
> 7. **It runs last unless you move it**: The card is at 100, so its tickets come after the 99 already ready. Drag it up on the board if you want it sooner.
>    Action: Nothing, unless you drag it.
>
> Proposals:
> - Backups on the Projects page and the desk (mockup)
> - F178, Backups on the dashboard: plan and three tickets (plan)
