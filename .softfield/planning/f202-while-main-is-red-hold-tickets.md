# F202: While main fails its tests, only the ticket that mends it runs

The planning thread behind F202's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-11 02:09

> Plan this card.

## The lead, 2026-11-11 06:45

> I've drafted ADR 47 and two lead tickets for F202. Both tickets pass pre-flight except for one thing: ADR 47 has to be accepted before their plan can be approved.
>
> 1. **What goes wrong today**: When main fails its tests, the runner holds the lead's tickets but still starts developer tickets. Each one is cut from a broken main, so it fails `all-tests` and ends up waiting on its branch after a full model run. Qwen takes up to an hour per run, and in f80-01 that meant 72 minutes plus $1.56 of Opus on work that was right. Each of those waits also replaces the list of checks main fails with `tests` alone, so a `layout` failure is forgotten and main is called mended while `layout` still fails.
>    Action: ADR 47 items 1 and 2; ticket f202-01.
> 2. **This changes a workflow rule, so it needs an ADR now**: The card's notes said to wait for the next ADR about a red main. But this changes ADR 29 item 7, and a workflow rule changes only through an accepted ADR. A small ADR of its own is cheaper than waiting: nothing else about a red main is planned. Pre-flight won't take the tickets until ADR 47 is accepted, so accept it first, then approve the plan.
>    Action: Accept ADR 47 (`softfield accept 47`), then press Approve on the plan.
> 3. **A gap I found: the mender can lock the line**: This goes past the card's notes. The mender is the ticket that would fix main. If its fix is incomplete, it fails the same check main fails, so today it waits for main, while main waits for it. Holding every other ticket would make that a full stop. The fix: the mender never waits for main, and a failure counts as a normal failed attempt. A blocked ticket then gets the lead's look from ADR 29.
>    Action: ADR 47 item 3; ticket f202-02.
> 4. **A repair ticket written after main went red is found**: Today the runner chooses the mender only once, at the moment main goes red. A repair ticket the lead queues after that is never recognised, so it would be held like everything else. The runner will now keep the failing output and look for a mender again at each pick, for as long as it has none.
>    Action: ADR 47 item 4; ticket f202-02.
> 5. **The cost: the line can stop**: With no mender, nothing runs until main is fixed. I still recommend it: today the line keeps running, but only fills branches that can't merge until main passes anyway. Your desk item will say 'no other ticket runs until main passes', and 'nothing would mend it yet' when there's no mender. The hold covers developer tickets only when main fails `tests`. A failure only in checks like `layout`, which look at a ticket's own changes, doesn't stop them.
>    Action: ADR 47 items 1 and 5.
> 6. **No mock-up**: No page changes layout. Only the words of the red-main item on your desk change (item 5), so there's nothing to draw.
>    Action: Nothing.
>
> Proposals:
> - ADR 47: While main fails its tests, only the ticket that mends it runs (adr)
> - F202: two lead tickets in the runner (plan)
