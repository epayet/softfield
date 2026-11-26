# F305: Find what writes terabytes to the SSD, and keep test temp files in memory

The planning thread behind F305's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-25 21:58

> I am a bit concerned looking at system monitoring that I'm writing terabytes of data to my disk probably from factory stuff. is it concerning for my ssd and is it needed

## The lead, 2026-11-26 00:52

> I couldn't measure the writes from here, so this plan measures first and then fixes the most likely cause. Both tickets pass the ticket check.
>
> 1. **Is it bad for the SSD?**: It depends on how much is written per day. A typical consumer 1 TB SSD is guaranteed for about 600 TB written; depending on the model that is anywhere from about 150 to over 1,000 TB. A few TB in total is under 1% of that, which is nothing to worry about. A few TB every week would wear out a 600 TB drive in a few years, which is worth fixing. The drive keeps its own wear figures, and those settle it.
>    Action: Open the Disks app, pick the SSD, open its menu and choose 'SMART Data & Self-Tests'. Send me 'Percentage used' (or 'Data units written') and say what period your system monitor's terabytes cover: since the last boot, or since the drive was new.
> 2. **Space is fine; it's the writes**: I checked the space today. /tmp holds 19.8 MB, the factory's temp folders 0.5 MB, the run logs 1.5 GB and the metrics database 14 MB. So F175, The factory cleans up its temp files, is still working. But free space doesn't show what was written and then deleted again, and that is what wears an SSD. I can't read the disk's write counters from here, so the factory can't tell you yet.
>    Action: Ticket f305-01: 'softfield look disk' shows GB written since boot and GB per day, and every check run ends with a line saying how much it wrote.
> 3. **The likely cause: the tests the factory runs again and again**: Since 12 November the line has run 20 to 24 hours on most days, with 65 to 116 jobs a day. Every check, by the gate or a developer, runs the whole test suite. That creates thousands of small git repos, databases and browser profiles and deletes them minutes later. On Ubuntu /tmp sits on the SSD, so all of it really gets written. Before F175's fix one run left about 2 GB behind. Run that many times a day and it plausibly adds up to terabytes a month. Other possible writers I'll check: Docker rebuilding a project's app each time main moves, the review's pictures (a new checkout and Python environment each time), and swap.
>    Action: f305-02 starts by measuring how much of each day's writes come from the checks, and names any other big writer with its number.
> 4. **Is it needed? Mostly not.**: The tests have to run, but their temporary files don't have to touch the SSD. They live for minutes and are deleted at the end of each job, so they can sit in memory. If the measurement confirms the checks are the main writer, the factory's temp folder moves to /dev/shm, which is in memory. It does so only when there are at least 4 GB free there, otherwise it stays on /tmp. It is still emptied after every job, as F175 does now. Nothing you keep moves: run logs, the database and pictures stay on the disk. If the tests turn out not to be the writer, nothing moves and the card names the real cause and its fix.
>    Action: Ticket f305-02, after f305-01.
> 5. **Better than making all of /tmp memory**: You could also switch the whole of /tmp to memory, as newer Ubuntu releases do. That would cover every program, but it is a system change for you to make, and with LM Studio loaded a large /tmp could push the machine into swap, which writes to the SSD again. Moving only the factory's own folder, with the 4 GB check, is the smaller change. f305-02 also records the most the folder grew during a run, so we'll know how much memory it really takes.
>    Action: Nothing, unless you'd rather make all of /tmp memory yourself.
> 6. **No mock-up**: Nothing on a page changes: the numbers go into 'softfield look disk', the check logs and this card. If you want the writes per day on a dashboard page, say so and I'll add a ticket with a mock-up.
>    Action: Nothing.
>
> Proposals:
> - Measure what the factory writes to the SSD, then keep test temp files in memory (plan)
