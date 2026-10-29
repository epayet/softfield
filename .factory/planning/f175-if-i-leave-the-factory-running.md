# F175: The factory cleans up its temp files, so the disk stops filling

The planning thread behind F175's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-26 22:52

> if i leave the factory running for a long time, the disk space goes away, probably lots on the tmp folder. i can see impact when i reboot computer, it takes a long time to boot next time, probably cleaning tmp folder. when i rebooted my computer last, there was 30GB of disk space that came back. make the factory less space hungry, or better at cleaning up

## The lead, 2026-10-27 09:39

> I've drafted a plan in three tickets. The cause I can see is that the runner force-kills every job when it ends, so nothing in the job gets to delete its temp files. I couldn't measure the 30 GB from here, so the plan measures first.
>
> 1. **What /tmp holds right now**: A few days after your last reboot, /tmp already holds about 117,000 files. They are: pytest's test folders (a few thousand small git repos; pytest keeps only its last three runs, so this part stops growing), 25 databases left by one dashboard test (one more each time the tests run), 23 Chromium folders left by browser tests, and small caches from node, uv and LM Studio. Ubuntu deletes /tmp only at boot. Deleting that many files is your slow boot.
>    Action: Nothing: the tickets below remove the cause.
> 2. **Why the factory leaves files behind**: When a job or check ends, the runner kills everything it started, at once and with no chance to clean up. That is on purpose: since early October it has stopped tests from running on for hours or days after their job. The cost is that a killed test or browser can't delete its temp files. Every timeout, stuck attempt or failed check leaves its files in /tmp until the next reboot.
>    Action: Ticket f175-02: each job gets its own temp folder, deleted when the job ends, however it ends. Starting the runner also deletes folders left by a runner that died (a reboot, a crash).
> 3. **The 30 GB may not all be /tmp**: This planning job can list files but can't size them, so I can't prove where the 30 GB were. A reboot also gives space back in two other ways. A program can keep a deleted file open, and the space only comes back when it stops. And the metrics database keeps a side file (its write-ahead log) that can keep growing while the dashboard reads; it shrinks back only when everything using the database closes. Fixing only /tmp could miss the real cause.
>    Action: Ticket f175-01 adds a read-only disk report that sizes each of those places. It records the numbers in the card before the fix. Ticket f175-03 measures again after the fix and either bounds what still grows or records that nothing does.
> 4. **Only the factory's own files are deleted**: The cleanup deletes only folders the factory made, all kept in one place under /tmp. Your browser's files, LM Studio's and other programs' files are never touched. The folder stays inside /tmp, so a reboot still empties it if anything goes wrong.
>    Action: Nothing: it is in the plan as decisions D1 to D3.
> 5. **Anything that touches your data becomes an ADR**: Every job's logs are kept forever, and the metrics database holds your threads and ratings. If the second measurement shows either one growing a lot, deleting from it is a data-loss decision, and that is yours to make.
>    Action: In that case f175-03 drafts an ADR for you instead of deleting anything itself.
> 6. **Move F175 up the board**: F175 sits at the bottom of the board, behind 73 ready tickets: about 39 hours of work at 32 minutes a ticket. The disk keeps filling during those 39 hours, and a full disk would stop the factory itself. The fix is small: three tickets, about an hour and a half.
>    Action: I recommend dragging F175 to the top of the board when you approve.
> 7. **One leaking test is also on F71's list**: The test that leaves a database in /tmp on every run is also one of the slowest (28 s). F71, the test-speed card, already plans to rewrite it in f71-03. Once f175-02 lands, the database it leaves is deleted at the end of each run anyway.
>    Action: Nothing extra: F71 keeps the speed part.
> 8. **No mock-up**: Nothing on a dashboard page changes. The disk report is a command the lead's jobs run.
>    Action: Nothing.
>
> Proposals:
> - F175: the factory cleans up its temp files, so the disk stops filling (plan)
