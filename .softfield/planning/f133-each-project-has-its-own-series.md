# F133: Each project gets its own card letter, and the factory/product area goes

The planning thread behind F133's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 04:30

> Plan drafted on plan/f133: one letter series per project, the factory/product area retired, four tickets and a board mock-up.
>
> 1. **A letter per project is the right fix**: I agree, and I'd keep letters rather than just adding the project's name in shared views. A card's key also appears where no project name sits beside it: ticket ids (m1-01-…), commit trailers, branch names, tags (m1-done) and conversation. One line in each project's settings fixes all of those at once. Softfield keeps f, Coucou keeps m, the test-factory-hello projects stay on m as you asked, and no key already given is renamed.
>    Action: Tickets f133-01 (the key comes from the project's series) and f133-02 (softfield init picks one).
> 2. **The factory/product area goes, and that is already agreed**: Read from the code: today the area picks the letter, sits in each card's header, is required on a bug ticket, colours, labels and filters the board, and is shown on the card page. On travel-companion's board right now, 'F7 factory: a map view of my trips' sits next to 'F6 product', and the legend says 'product (for Mum)': the word means nothing there any more. ADR 30, which you accepted, already says 'a card's area becomes its project', so no new ADR is needed. The task format just follows it, and a bug no longer needs area:.
>    Action: Tickets f133-03 (board) and f133-04 (runner and task format).
> 3. **It builds on F171, Each card once on the board**: F171's ticket f171-04, 4th in line, adds an area setting to each project so that travel-companion's next card is an M again. F133 then swaps that line for series, so a few lines get written twice. I'm leaving f171-04 in place: it fixes travel-companion's confusing letters now, while F133 sits at the bottom of the board. f133-01 waits for it.
>    Action: f133-01 depends_on f171-04.
> 4. **Which letter for travel-companion?**: I recommend t: its next card is T1, and its M1 and F1–F9 keep their keys. The alternatives are to keep m (the next card is M2, as f171-04 will make it, but then it shares m with Coucou) or two letters such as tc. Either way it's one line in travel-companion's own settings file, which no ticket in this repo can write, so the next terminal session adds it once F133 lands. I'll put that in the review's What next.
>    Action: Your choice: t (recommended), m, or tc.
> 5. **How init picks a new project's letter**: It tries the name's first letter (hello gets h), then its first two letters (hello-2 gets he if h is taken), then the first free letter. It never picks f, m or a letter another project uses. The setup session may change it before the first card, which is then named <letter>1 instead of always m1.
>    Action: Ticket f133-02, D3 in the card's doc.
> 6. **The board without areas**: The mock-up is drawn on travel-companion's real board. Every card that isn't a bug gets the same yellow edge, the one Softfield's cards already have. A card's small line shows only its place and key. The filter becomes All and Bugs, the legend keeps only 'bug' and 'growing', and the card page loses its Area row. One thing stays: in a milestone review's idea plates, factory and product still decide which project an idea is planted in, and F164 owns that.
>    Action: Mock-up .factory/cards/f133-mockup/board.html; ticket f133-03 (developer).
> 7. **Cost and when it runs**: Four tickets: three for the lead, all in the runner, and one for a developer on the dashboard. At about 32 minutes a ticket, that's roughly two hours of line time. The card sits last on the board, so it runs after everything ahead of it unless you drag it up. Nothing here needs a pause: no F133 ticket is in line yet.
>    Action: None, unless you want it sooner: drag the card up on the board.
>
> Proposals:
> - F133: each project has its own series letter, and the area goes (plan)

## The lead, 2026-10-27 09:29

> Merged F155 here: The owner planted: no product vs factory split on the board, but it helps in the reports. Later message: remove the whole 'for Mum' thing and the area splits and filters on the board. Nothing was answered on F155. Still open: whether the board keeps a Bugs filter or loses every filter.

## The owner, 2026-10-27 09:29

> From F155, merged here:
> We don't need the product vs factory on the board. But in the reports it's helpful

## The lead, 2026-10-27 18:56

> I've added your note to the plan. The board drops the factory/product split, and the reports keep it. The tickets and the mock-up don't change.
>
> 1. **Reports keep the product and factory split**: I agree. That split in the reports is a different thing from a card's area. When a milestone review ends with 'What next', it gives product suggestions and factory suggestions. Each idea plate then plants a factory idea in Softfield and a product idea in the project that was reviewed. That routing really is useful. Neither of these reads a card's area, so nothing in F133 touches them. I wrote that down as D6 on the card so no ticket removes the split by accident.
>    Action: D6 added to the card's doc; no ticket changes.
> 2. **Off the board: only the factory/product split**: I read 'we don't need the product vs factory on the board' as covering the split only. So f133-03 and the mock-up stay as they are. The Factory and Product filters go, along with the coloured edges, the labels, the 'product (for Mum)' legend entry and the Area row on the card page. The Bugs filter and its striped edge stay. Bugs are a different kind of card, not an area. If you want the Bugs filter gone too, say so here and I'll change the ticket and the mock-up.
>    Action: Nothing, unless you want Bugs gone too.
> 3. **Travel-companion's letter is still open**: I recommend t: its next card would be T1, and M1 and F1–F9 keep their keys. The other choices are m (shared with Coucou) and tc. If you don't answer, I'll go with t when F133 lands.
>    Action: Your choice: t (recommended), m, or tc.
>
> Proposals:
> - F133: each project has its own series letter, and the area goes (plan)

## The owner, 2026-11-05 11:03

> I sent back your proposal “F133: each project has its own series letter, and the area goes” (plan-f133).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-05 11:20

> I checked the plan against main and updated the tickets, mock-up and card doc. You can't approve it yet, though, because this branch clashes with main (point 1).
>
> 1. **You can't approve this plan yet**: This branch left main before the move to .softfield, so it clashes with main and Approve refuses it. The fix is already queued: f139-03, a ticket on F139, The factory folder should be .softfield, which rebuilds clashing plan branches on main. It is 7th in line, and F133's own commits move across with it. I can't rebuild the branch from a planning reply. Your note from F155 was at risk in that rebuild, so I copied it word for word into this branch's doc.
>    Action: Nothing for now. Once f139-03 lands, this page tells you what to press, and I check the plan once more when that runs.
> 2. **Nothing to renumber or drop**: No F133 ticket exists on main, so f133-01 to f133-04 keep their numbers. None of the work has been done either: the letters still come from the area in the runner, and the board still shows and filters by it. f171-04 (on F171, Each card once on the board) hasn't landed, so f133-01 still waits for it. It is now 22nd in line, not 4th.
>    Action: Tickets keep their numbers; f133-01 keeps its wait.
> 3. **What main changed in the tickets**: The setup and task format instructions moved to runner/instructions/, and the first card is now step 7 of setup. A thread's title code moved from planning.py to thread.py, and it stamps 'factory' beside the title, so that stamp goes too. The board gained a developer's view lever, which stays. The planner's prompt also asks for area: on a bug, so f133-04 now covers that. Ready tickets carry area: factory, so an unknown value must stop failing them. The fast lane mark is written after a card's Area line and falls back to Priority, so new cards work; f133-04 keeps that code for old cards and tests it. The ticket check passes.
>    Action: All four tickets updated.
> 4. **The weekly reports keep the split too**: Since your note, F59, Periodic review of the factory, has planned weekly reports with 'Ideas for the factory' and 'Ideas for <project>'. They send an area when you plant an idea from them, and so will the review's idea plates. So F133 now ignores an area on a plant and never refuses it. Your split in the reports stays, and each idea still goes to the right project.
>    Action: D2 and D6 updated in the card's doc.
> 5. **Travel-companion gets t**: You didn't choose otherwise, so I'm going with t as I said I would. Its cards now run up to F12, so its next card is T1, and M1 and F1–F12 keep their keys. The line goes into its own settings file in a terminal session once F133 lands. Until then, f171-04 makes its next card M2.
>    Action: Recorded in the plan; say so here if you'd rather have m or tc.
> 6. **Mock-up redrawn from today's page**: It now shows travel-companion's board as it is today, including F10, F11, F12 and the developer's view lever, plus a card's page and a thread's title. The card also lists these pages for the review's before and after pictures: the board, F133's card page and this thread. I couldn't open the mock-up in a browser from this job, so tell me if anything looks wrong.
>    Action: Mock-up .softfield/cards/f133-mockup/board.html; ticket f133-03 builds it.
>
> Proposals:
> - F133: each project has its own series letter, and the area goes (plan)
> - F133 mock-up: the board without areas (mockup)

## The owner, 2026-11-05 11:31

> I sent back your proposal “F133: each project has its own series letter, and the area goes” (plan-f133).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-05 15:51

> Main has changed since my last check only on the Agents page, so the plan and tickets stay as they were and the blocker below remains.
>
> 1. **Refresh can't clear this until the branch is rebuilt**: Since my last check, main has only gained work on the Agents page from F179, How is Sonnet doing as a lead, and F133 doesn't touch that. So nothing needed renumbering or dropping, the four tickets stay as they are, and they still pass the ticket check. Approve is still blocked for the reason I gave last time: this branch clashes with main, and a planning reply can't repair that. The repair is f139-03, on F139, The factory folder should be .softfield, and it hasn't landed yet. Sending the plan back again before then costs another lead reply and changes nothing.
>    Action: Wait for f139-03; its page will then say what to press, and I'll check the plan once more when that runs. If you want it sooner, drag F139 up the board.
>
> Proposals:
> - F133: each project has its own series letter, and the area goes (plan)

## The owner, 2026-11-14 10:19

> I sent back your proposal “F133: each project has its own series letter, and the area goes” (plan-f133).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-14 10:33

> I've updated the four tickets, the mock-up and the card doc to match main, but Approve will still refuse the plan because of one leftover file (point 1).
>
> 1. **One leftover file still blocks Approve**: f139-03 rebuilt this branch on main today, so the clash is gone. But it left one file at its old place: the mock-up's first copy, .factory/cards/f133-mockup/board.html. Approve refuses a plan that changes anything outside the drafts' folders. A planning reply can only write files, not delete them, so I can't remove it from here. I've written the up-to-date mock-up at its right place. Reject is no way out either: on a card with nothing built yet, it removes the card and your notes with it.
>    Action: In your next terminal session (softfield lead), I remove that one file with a single commit on plan/f133. After that, Approve goes through.
> 2. **The rebuild should carry every old file across**: The rebuild moved the tickets and the card doc but missed a folder that a draft created before the move. Plan branches from the same time may hit the same snag. The fix is in the runner: after the replay, the rebuild moves anything still under .factory/ to .softfield/, so no branch is left holding a stray file. Text ready for the Plant box: 'A rebuilt plan branch can keep a file under .factory/ (plan/f133 kept its mock-up folder) and then can't be approved: after the replay, move whatever is left under .factory/ to .softfield/.'
>    Action: Plant that note if you want it fixed for the other branches; it doesn't block F133 once point 1 is done.
> 3. **Dropped and updated against main**: Nothing in F133 has been done on main, so no ticket numbers change. f171-04 is done: it added project_area in the runner's planner and area = "factory" in Softfield's settings. So f133-01 no longer waits for it and replaces those two with project_series and series = "f". The settings paths now point at .softfield/.
>    Action: f133-01 updated.
> 4. **Three tickets now wait for work that changes the same code**: F222, When plans get approved, takes the priority number out of card headers, the card page and the same runner files. So f133-03 waits for f222-03 and f133-04 for f222-04. f133-04's check no longer expects a 'Priority: 100' header. F236, softfield init adds a project, moves adding a project to the factory from init to a new softfield create, so f133-02 waits for f236-01 and picks a letter no project in the factory uses. All three are ahead in line already, so the waits cost no time.
>    Action: f133-02, f133-03 and f133-04 updated.
> 5. **Coaster-ranker shows the problem too: which letters?**: Since we last spoke, F171's ticket made travel-companion plant M2 and M3, and a new project, coaster-ranker, runs M1 to M12. So M2 now names a card in three projects. Like Coucou, both keep their old keys either way. I recommend t for travel-companion and c for coaster-ranker, so their next cards are T1 and C1. The alternative is to leave them on m and give letters only to new projects. That is less to change, but M-numbers stay shared by four projects.
>    Action: Your choice: t and c (recommended), or leave both on m. Each is one line in that project's own settings, added in a terminal session after F133 lands.
> 6. **Mock-up redrawn from today's board**: The mock-up is redrawn from travel-companion's board as it is today: the bug seed marked 'bug · product', F7 and M2 side by side, F11 waiting for your sign-off, and the new 'working now' legend entries, which stay. The card page still shows Priority because F222 changes that row, not F133. I couldn't open the mock-up in a browser from this job.
>    Action: Mock-up .softfield/cards/f133-mockup/board.html; ticket f133-03 builds it.
>
> Proposals:
> - F133: each project has its own series letter, and the area goes (plan)
> - F133 mock-up: the board without areas (mockup)
