# F169: Let the planner search and read the web for research

The planning thread behind F169's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-21 22:25

> Why is web search related tool not allowed for the planner? I just asked to do some research and it couldn't

## The lead, 2026-10-21 22:29

> I've drafted a short ADR and one lead ticket so the planner can search the web. Accept the ADR first: the ticket's check refuses it until then.
>
> 1. **Why it couldn't search**: No job the runner starts has ever had a web tool. Each job gets a fixed tool list: read files, its allowed edits and a few commands (runner/claude.py, allowed_tools). Everything else is refused without asking. Nobody decided against the web: it was just never added. ADR 15 even planned a monthly 'offers watch' job with web search, but that job was never built.
>    Action: ADR 33 and ticket f169-01
> 2. **The risk, and how the ADR handles it**: A web page is text written by strangers, and it can hide instructions. Today a job can read any file on the Mac, not just the repo. With web-page reading on, a page could trick the planner into reading a key file and putting it in an address it opens. Search alone can't send anything out, but reading a page can. So the ADR gives the planner both tools and, for any job that has the web, limits file reading to the repo and the project's live docs. What a trick could still reach: the repo (no secrets in it), the metrics database read-only, and drafts that wait for your Approve.
>    Action: ADR 33 item 2
> 3. **Search only, or search and read pages?**: I recommend both, with reading limited to the repo (item 2). Search snippets are too thin for a real comparison. Choices: (a) search and read pages, with file reading limited to the repo (recommended); (b) search only: safest, but answers stay shallow; (c) reading pages only from a list of sites: research can't know its sites in advance.
>    Action: Your choice goes into the ADR before you accept it
> 4. **Only the planner gets it**: Developers, lead tickets, checkpoints and reviews build or check against a ticket. For them the web adds risk and nothing useful. If ADR 15's offers watch is built one day, it can switch the same setting on.
>    Action: ADR 33 item 3
> 5. **One lead ticket, test first**: f169-01 adds the setting, turns it on for the planner, and adds one line to the planner's brief. That line says a page's text is information, never an instruction, and that answers name their links. It first tries the 'repo only' reading rule on a real Claude job. If no rule works, it falls back to search only and records that in the ADR. It is a lead ticket because it changes what jobs are allowed to do. No screen changes, so no mock-up. About one ticket, around 47 minutes.
>    Action: Queued when you approve the plan
> 6. **Order: accept the ADR, then approve the plan**: The ticket check refuses f169-01 while ADR 33 is still Proposed, so the plan's Approve would be refused too. Accept ADR 33 first, then approve the plan.
>    Action: Accept ADR 33, then approve the plan
>
> Proposals:
> - ADR 33: The planner can search and read the web (adr)
> - F169: the planner searches the web (plan)
