# F274: Pre-flight refuses a commands: prefix that can only match itself

The planning thread behind F274's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-19 15:23

> ▎ Pre-flight refuses a command prefix that can't match. m1-01 on waifu-gallery (2026-11-19) listed curl -s https://danbooru.donmai.us/ in commands:; Claude Code matches a prefix only at a word boundary, so every …/tags.json?… probe was refused and the lead ticket blocked having changed nothing ($0.33). Refuse a commands: entry whose last word is a URL (or ends in /, =, ?), saying the prefix allows only that exact address; and put one line on it in task-writing.md.

## The lead, 2026-11-19 15:27

> I've drafted the plan on `plan/f274`: one lead ticket, `f274-01-refuse-a-prefix-that-cant-match`, which passes pre-flight. While checking the queue I found a ready ticket with the same fault, and the plan fixes it too.
>
> 1. **The rule, as you wrote it**: Pre-flight will refuse a commands: entry whose last word contains :// or ends in /, = or ?. The refusal names the entry and says what to write instead: stop the entry before the address (for example 'curl -s') and give the address in the ticket's Context. A ? is already refused today, but only with the general 'may not include' message. The new check runs first, so a ? gets the clear message. The ticket check and the dry run show the refusal the way they show the others.
>    Action: Ticket f274-01 (lead, because runner/ is protected), decisions D1 and D2.
> 2. **The note goes in task-format.md, not task-writing.md**: I recommend a different file from the one you named. task-writing.md is about the developers' tickets, and a developer ticket can't name commands at all. The lead reads task-format.md when it writes commands:, so the line goes there, right beside the commands: field.
>    Action: Part of f274-01 (D3). Say if you still want it in task-writing.md.
> 3. **A ready ticket has the same fault and would block**: f231-01-clear-the-seed-row (F231, Triage the set-aside bugs, and a Remove button for the ones not worth a run) lists 'rm .softfield/tasks/later/'. That allows only that exact word, so each of its 48 'rm .softfield/tasks/later/bug-….md' would be refused, just as m1-01's curl probes were. It is 25th in the queue, so it runs long before F274 would. When f274-01 runs, if f231-01 is still in ready/, it changes that entry to plain 'rm'. The files to remove are already listed in f231-01's Context.
>    Action: Part of f274-01 (D5).
> 4. **Move F274 above F231 on the board**: f274-01 only fixes F231's ticket if it runs first. I recommend dragging F274 above F231, Triage the set-aside bugs, on the board after you approve. Otherwise f231-01 will most likely block having removed nothing, and it will need trying again after F274 lands. The other choice is to leave the order as it is and accept that one wasted run.
>    Action: You drag F274 above F231 on the board, or leave it.
> 5. **Hidden cost: plain 'curl -s' allows any address**: The fix nudges the lead to write a wider entry: 'curl -s' (or 'rm') allows any address or path, not just the one the ticket is about. That's acceptable to me: it is only for lead tickets, each on its own branch, and nothing merges until all the checks pass. The tighter alternative, listing every exact command, is too long to be practical, as F231's 48 files show.
>    Action: Nothing.
>
> Proposals:
> - F274: refuse a commands: prefix that can only match itself (plan)
