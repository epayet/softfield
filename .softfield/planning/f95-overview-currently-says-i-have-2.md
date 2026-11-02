# F95: overview currently says i have 2 things to sign off, but i…

The planning thread behind F95's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-10 07:51

> overview currently says i have 2 things to sign off, but i see only 1 'finish to talk through' on my desk

## The lead, 2026-10-10 07:55

> Read from the code: the Overview and the desk count sign-offs from two different sources. I drafted a one-ticket fix on `plan/f95`; nothing is queued until you approve.
>
> 1. **Why the Overview says 2 and the desk says 1**: They read two different things. The desk's 'Finished, to talk through' is worked out live: every ticket done, the review's sheet stored, not signed off yet. The Overview's Needs you also draws one row per sign-off item the runner stored when it gave a milestone's verdict ('ready for sign-off'), and that row stays open until the milestone is signed off. So a milestone that got new tickets after its verdict, or whose review has no sheet, keeps its row on the Overview while the desk no longer lists it.
>    Action: Ticket f95-01-sign-offs-counted-once (drafted, a small developer ticket): the Overview stops drawing the stored sign-off rows, and the desk's entry in Needs you is the one place a sign-off shows.
> 2. **I couldn't see which milestone is the extra one**: This job can't read the metrics database, so I know the mechanism from the code but not which of your two rows is the stale one. On the Overview it is the row with a 'signoff' pill whose milestone isn't under 'Finished, to talk through' on your desk.
>    Action: Nothing needed for the fix. If you tell me its name on this thread, I'll check whether it really is finished and should be on the desk instead.
> 3. **Risk: a sign-off that shows nowhere**: If the extra milestone is truly finished but its review has no sign-off sheet, the desk doesn't list it, and after this fix the Overview wouldn't either. I still recommend the fix: one source is the only way the two pages can't disagree, and the review job writes the sheet for every milestone since F50, so this should only touch older ones.
>    Action: Nothing now. If point 2 turns out to be that case, a second ticket: the desk lists a finished milestone with no sheet as 'finished, review sheet missing'.
> 4. **The stored rows stay in the runner**: I left the runner alone: it still stores the sign-off item at each verdict, because notifications read it. The alternative, having the runner close stale rows, is more code in the runner for the same result on screen.
>    Action: Nothing.
>
> Proposals:
> - F95: sign-offs counted once on the Overview (plan)

## The owner, 2026-10-10 08:32

> On point 2: Why can't this job check the database?

## The lead, 2026-10-10 08:32

> 1. **Why this job can't check the database**: By how the runner starts it. A planning job gets a short list of tools (runner/loop.py, run_planner): read, search and list files, edit drafts on the card's plan branch, and four git commands (diff, log, show, checkout of the plan branch). Anything else is refused without asking. The metrics database is one binary SQLite file: reading it needs a command (sqlite3, or Python), and none is on the list. So I can read the code that draws your Overview, but not the rows it draws from.
>    Action: Nothing for F95: its ticket fixes the mismatch whichever milestone is the stale one.
> 2. **This gap keeps costing you answers**: It isn't the first time: F26's review says its times came from commits because the job couldn't read the database, and F94's mock-up used example rows for the same reason. You asked for answers from the code and the queue, not the plan alone, and a planning job can only do the first half. Here it meant I could explain the mechanism but not name your second sign-off.
>    Action: A seed (proposed below): one read-only runner command that prints what the dashboard shows (Needs you, the desk, the queue, the field), allowed for planning and review jobs.
> 3. **Why a command, not the database itself**: I recommend against letting these jobs run sqlite3 or Python on the database. It holds everything (your threads, requests, ratings), a headless job writing free SQL is a much wider permission than it needs, and it would read raw tables, not what your pages show, so it could repeat the very mismatch F95 is about. A command built on the dashboard's own functions prints exactly what you see, read-only. The cheaper alternative is to paste those facts into every planning prompt: no new permission, but it costs tokens on every reply, needed or not.
>    Action: Part of the seed: the command as the recommendation, the prompt snapshot as the alternative to choose between when it is planned. Adding a command to a headless job's list is a permission change, so its plan will ask you.
>
> Proposals:
> - Planning and review jobs can read what the dashboard shows (seed)

## The owner, 2026-10-10 08:53

> Could it have read only access to the db somehow? Or maybe a copy when the job starts? If it does have safe access to the db then is there still a point sharing how the dashboard looks like right now? Sounds expensive.  If cheap, why not do both then maybe?

## The lead, 2026-10-10 08:54

> 1. **Read-only access: yes, and it's the better of your two**: SQLite can open a file read-only, and on top of that be told to refuse every write. The safe way to give that to a job is our own small command (say `uv run runner query "SELECT …"`) that opens the database that way and prints the rows. I'd not allow the stock `sqlite3` program instead: even in read-only mode it has side commands that run a shell or write files, and the runner's permission rules only check how a command starts.
>    Action: Goes into the seed (revised below) as its first decision.
> 2. **A copy at job start: I'd skip it**: A copy protects the live database from writes, which read-only already does, and the job would still need a command to read the copy. It adds a file to make and clean up per job, and a copy of your threads lying around. Its one real advantage is a frozen picture while the runner keeps writing; a planning job doesn't need that.
>    Action: Nothing; recorded in the seed as the alternative turned down.
> 3. **Is the dashboard's view still worth it? Yes, a small one**: The raw tables don't hold what your pages show. Your desk isn't stored anywhere: it is worked out each time from tickets, reviews and requests. F95 is exactly that: with only the tables I'd have seen two open sign-off rows and still had to redo the desk's reasoning by hand to tell you which one it lists, with a fair chance of getting it wrong.
>    Action: Goes into the seed as its second decision: a `facts` form of the same command, printing Needs you, the desk, the queue and the field from the dashboard's own functions.
> 4. **It's cheap, so both**: What I called expensive was pasting the facts into every planning prompt, used or not. As a command it costs nothing until a job calls it, then a few hundred to a couple of thousand tokens of text, cents on a reply that already costs far more. The building cost is one small ticket: both forms reuse code that exists. So I agree with doing both, as two forms of one command.
>    Action: The seed now says both, on demand, nothing added to prompts.
> 5. **What you'd be agreeing to**: A new permission for headless jobs: planning and review jobs could read everything in the metrics database, including your planning threads and ratings. They can't change it, and nothing leaves the machine beyond what a planning job already sends to Claude (your messages on its thread). I recommend it for planning and review jobs only, not developers' jobs, which have no use for it.
>    Action: An ADR item in the seed's plan, since it is a permission change: you accept it there before any ticket is queued.
>
> Proposals:
> - Planning and review jobs can read what the dashboard shows (seed)

## The owner, 2026-10-10 09:14

> On point 3: This does not seem like it would scale? If we add features, then we'll have to update the list of what gets shown in the dashboard. Maybe that's fine if it's an optional help but it seems like something to remember to do when new features to the factory get added and we want the planner to see what's going on

## The lead, 2026-10-10 09:14

> 1. **You're right: a hand-kept list would rot**: As I described it, the command would print a fixed set (Needs you, the desk, the queue, the field), and every new page or panel would need someone to remember to add it. Nobody would, and the planner would quietly see an older factory than you do. That is the same kind of drift F95 is about.
>    Action: I drop the fixed list from the seed (revised below).
> 2. **Better: let the job open the dashboard's own pages**: Instead of a list, the command takes a page's address and prints that page as plain text: `uv run runner page /planning`, `/`, `/milestones/f95`, and any page added later. It asks the dashboard's own code for the page, the way your browser does, so there is nothing to keep in step: a new feature is visible to the planner the day it is visible to you. It only ever reads (it refuses anything but opening a page, so it can't press Sign off or Approve).
>    Action: Goes into the seed as its second decision, replacing the fixed list.
> 3. **Cost and one limit**: Same as before: nothing until a job calls it, then one page of text. The limit: what is drawn in the browser by script (the factory floor) isn't in the page's text; for that the command prints the data the drawing is made from, which the dashboard already serves. A page can also be long, so the command cuts the styling and scripts and keeps the words.
>    Action: Noted in the seed; the ticket's test opens the Overview and the desk and checks their words come out.
> 4. **Still both, and now neither needs upkeep**: Read-only questions to the database stay for what no page shows (times, counts across milestones, as F26's review needed); the page form answers 'what does the owner see right now'. Both follow the factory as it grows without a list to maintain.
>    Action: Nothing more: the seed carries both, and the permission stays an ADR item for you to accept in its plan.
>
> Proposals:
> - Planning and review jobs can read what the dashboard shows (seed)

## The owner, 2026-10-10 10:01

> This is not a seed anymore but we're getting closer to making a plan instead
>
> On point 2: Is that truly the best way for the planner to 'see' the current dashboard in places? I wonder if there could be better tooling, browser mcp or something. Perhaps what you said is fine to begin with?
> On point 3: Yeah that's related to my previous command. If the goal is to have the information rather than how it looks like then that's fine, although there could questions around things looking bad that it won't be able to answer? But perhaps more expensive?

## The lead, 2026-10-10 10:03

> This turns the seed into a plan on F95: an ADR for the new permission, one lead ticket, and the card's doc updated. Nothing is queued until you approve.
>
> 1. **From seed to plan, on this card**: Agreed. I planned it here, not as a new card: it came out of F95's question and is one ticket. F95 now has two parts: the Overview counts sign-offs once (f95-01, unchanged), and planning and review jobs can look at the database and the dashboard (f95-02, new). The seed I proposed earlier is replaced by this plan.
>    Action: Plan revised (below). Ignore the earlier seed proposal 'Planning and review jobs can read what the dashboard shows'; if it still shows on your desk, send it back.
> 2. **Is text of the page the best way to 'see'? For information, yes**: For 'what is on my desk, what does the Overview say', the page's words from the dashboard's own code are the cheapest and most exact thing, and work with any frontier. I recommend against a browser for the job (a browser MCP) for now, for three reasons: a browser can press Sign off and Approve, where this command can only open a page; it ties the workflow to one frontier's tooling, which ADR 02 wants to avoid; and it is much more to set up for headless jobs.
>    Action: ADR 28 records it under 'Alternatives turned down'. Start with the text, as you suggest.
> 3. **Questions about looks: not answered yet, and there is a cheap next step**: You're right that the text can't answer 'this looks bad' (an overlap, a colour, the phone layout). The middle way is a screenshot form of the same command: the browser tests already drive a real browser, so the command can save a picture of a page for the job to read, with no way to click. Cost: roughly one to two thousand tokens per picture, a few cents, only when a job takes one. I left it out of this plan: it adds a browser to the runner's own commands, and no question has needed it yet.
>    Action: In ADR 28 under 'Later' and in the card as D4. If you'd rather have it now, say so and I add a third ticket.
> 4. **The command, as planned**: `uv run runner look`, two forms: `look sql "SELECT …"` prints rows, with SQLite itself refusing anything but a read; `look page /planning` prints any dashboard page as text. It writes nothing, and unlike other runner commands it doesn't apply your waiting requests first. One thing I found while writing the ticket: a read-only connection alone isn't enough, since one SQL command (ATTACH) can still create a new file, so the ticket blocks that inside SQLite and tests it.
>    Action: Ticket f95-02-lead-jobs-can-look, a lead ticket: all of runner/ is protected, so Claude writes it test-first.
> 5. **What you accept with ADR 28**: Planner and review jobs can read everything in the metrics database, your planning threads and ratings included, and can't change any of it. Developers' jobs, checkpoints and escalations don't get it.
>    Action: ADR 28, status Proposed. Approving the plan accepts it; f95-02 waits for that. I recommend approving both together.
> 6. **Cost**: f95-01 is one developer run, as before. f95-02 is one lead job on Opus, a small new module plus two lines in the job lists; I'd expect it at about the size of a normal lead ticket. The two tickets don't depend on each other.
>    Action: Nothing.
>
> Proposals:
> - F95: sign-offs counted once, and the lead can look (plan)
> - ADR 28: Planning and review jobs can look at the database and the dashboard (adr)

## The lead, 2026-10-12 19:08

> Approved by the owner on 2026-10-12: approved plan/f95: queued f95-01-sign-offs-counted-once, f95-02-lead-jobs-can-look

## The owner, 2026-10-13 18:11

> From F115, merged here:
> I may have asked this before but why are there things to to sign off in overview needs you but nothing on my desk

## The lead, 2026-10-13 18:12

> You did ask before, twice, and both fixes are planned but neither is built yet. I drafted a replan that moves F95's two tickets up; both pass pre-flight, and nothing changes until you approve.
>
> 1. **Yes, you asked before, and the answer is the same cause**: Twice: here on F95, Sign-offs counted once and the lead can look, and on F110, Ripe on the board but no Sign off button. Needs you on the Overview lists sign-off rows the runner stored when it gave each milestone's verdict, and they stay until that milestone is signed off. Your desk works it out fresh each time, with a stricter rule. So a milestone that got new tickets after its verdict, or has a ticket set aside, keeps its row on the Overview and is absent from your desk.
>    Action: Nothing new to plan: the two fixes below already exist.
> 2. **Why you still see it: neither fix is built**: Both tickets are still waiting in the queue. `f110-01-ripe-is-one-rule` makes the desk list a finished card that has a ticket set aside (F31, When I click on Approve plan, is one). `f95-01-sign-offs-counted-once` then removes the stored rows from Needs you, and it waits for the first, so that no sign-off ends up showing in neither place. F95 sat at priority 3, behind about a dozen priority 1 tickets that can run now, at about 30 minutes each.
>    Action: The replan below moves F95's tickets up.
> 3. **The look ticket goes first, as you asked on F110**: On F110 you said to prioritise the ticket that lets me read the database. It never got a priority of its own, so it stayed at F95's 3. I set `f95-02-lead-jobs-can-look` to priority 0: with nothing in flight, it is the next ticket the runner takes. It is a lead ticket on Opus.
>    Action: In the replan. Once it is merged I can name which milestones are behind the rows you see, on this thread.
> 4. **The sign-off fix moves up too, but waits for F110's ticket**: I set `f95-01-sign-offs-counted-once` to priority 1, from 2. It still can't run before `f110-01-ripe-is-one-rule`, which belongs to F110, Ripe on the board but no Sign off button, and which I can't change from this thread. That one is already at priority 1 and takes its turn among the priority 1 tickets. I'd keep the wait: dropping it risks a finished card showing nowhere for a few hours.
>    Action: In the replan. If you want it sooner still, say so here and I'll plan the order change for F110's ticket where it can be made.
> 5. **I still can't tell you which milestones they are**: For the same reason as last time: this job can't read the database until the look ticket is built. From the code, the likely ones are cards that were ready for sign-off once and then got more tickets, or have a ticket set aside. That is a guess, not a reading.
>    Action: Fixed by point 3.
> 6. **Pause the factory before approving**: The replan changes two waiting tickets, and the line is idle now, so it may pick one up while you read. Pause it from the dashboard first; approving the replan lifts your pause.
>    Action: Pause, then approve.
>
> Proposals:
> - F95, Sign-offs counted once and the lead can look: both tickets move up (replan)
