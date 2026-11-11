# F85: Real before and after pictures of the changed pages when you sign a card off

The planning thread behind F85's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:28

> Plan this card.

## The lead, 2026-10-27 03:54

> I've drafted the plan for F85: the card's plan, a mock-up and three tickets, all on `plan/f85`. Nothing is queued until you press Approve.
>
> 1. **What you'll get**: When a card that changed a page is ready for sign-off, its page gets a 'Before and after' panel right under 'What changed'. It shows real pictures of each page the card changed, as it was and as it is now. It has the same Before / After switch as the mock-ups, plus a Phone / Wide switch. On a wide screen Before and After sit side by side, and a tap opens a picture at full size. A card that changed no page shows nothing new. F72 (mock-ups by default) and ADR 28 (jobs can look) had both put this off until now.
>    Action: Plan with three tickets, f85-01 to f85-03.
> 2. **The runner takes the pictures, not Claude**: The runner takes them itself at the review, in a headless Chromium. That browser is already installed for the tests, it can't press anything and it opens no port. No job gets a browser, so ADR 28's refusal of one still holds and nothing here needs a new ADR. It costs seconds per review and no Claude tokens.
>    Action: f85-01.
> 3. **Before is drawn later, on today's data (I'd do it this way)**: The obvious way is to take the 'before' when the card starts. Two problems with that: the runner has no moment for it (the start tag is often set afterwards), and the data would be days older, so every number would differ as well. Instead, the review checks out the code as it was when the card started and draws both pictures from one copy of today's database. The only thing that differs is the code. The risk is that the old code may not understand a newer database. Then the panel says 'The page before couldn't be drawn' and still shows the after. A page that is new with the card says 'This page didn't exist before'.
>    Action: D2 to D5 on the card, f85-01.
> 4. **Which pages: the planner lists them**: Whenever the planner draws a mock-up, it also adds a short 'Before and after' list of page addresses to the card's doc. That list is the 'whenever relevant': no list, no pictures. The runner doesn't guess pages from the changed files, because there is no reliable link from a template to an address. F85 lists its own card page, so its sign-off is the first test. Cards ready for sign-off today, like F172 (Mark a card to use Claude's reserve), don't get pictures. My recommendation is to start with the next cards rather than add lists to old ones by hand.
>    Action: f85-03 changes the planner's brief and lead.md.
> 5. **The review checks the after pictures against the mock-up**: The review opens the after pictures next to the mock-up you approved. It writes one line at the end of 'What changed': it matches, or this is what differs. A clear difference becomes a should-fix finding, which the review's next round fixes before you sign off. That's about eight pictures per round for a two-page card, a few cents. I'd do it: without that line, the pictures only show you what the text already says.
>    Action: f85-03 (the review's brief).
> 6. **Your data stays on this machine**: The pictures show your dashboard, planning threads included. They are kept next to the database on this machine and are not in git. The temporary copy of the database is deleted once the pictures are taken. The review sends only the after pictures to Claude, and it can already read the same content as text.
>    Action: Nothing.
> 7. **All three tickets go to the lead**: f85-01 and f85-03 change the runner, which is protected. f85-02 adds the address that serves the pictures from disk. I'm keeping that with the lead because it has to refuse every file except the pictures: that's a security joint, not just a template. Roughly three lead tickets, about 1.5 hours of work. 02 and 03 wait for 01.
>    Action: Nothing.
> 8. **Factory pages only, for now**: Product work is on hold, so the coucou app's pages aren't pictured. When product work resumes, the same script can take them.
>    Action: Under the card's 'Later'.
> 9. **Mock-up: F172's page with the new panel**: Today is copied from F172's real card page, which is waiting for your sign-off now. Proposed adds the review's one line and the 'Before and after' panel, with F172's two changed pages (its card page with the new lever, the board with the new plate) and a page that didn't exist before. The small drawings stand in for the real pictures. The new parts have a dashed green outline.
>    Action: f85-02 builds from it.
>
> Proposals:
> - F85: real before and after pictures at sign-off (plan)
> - Before and after on a ripe card's page (mockup)

## The owner, 2026-10-27 08:07

> On point 8: will this work for other projects like travel companion. i essentially want screenshots of the product, whether the product is softfield or travel-companion or coucou

## The owner, 2026-10-27 08:07

> I sent back your proposal “Before and after on a ripe card's page” (f85-mockup).
> - On its key point 2 (Proposed): on sections that have urls, make then clickable to open on a new tab for me to have a look myself when relevant

## The lead, 2026-10-27 14:08

> I've reworked the plan so pictures work in every project, and drafted ADR 35 for the parts that need your yes (each project's own setting, and products shown on sample data only). The plan's tickets pass their checks except one, which needs ADR 35 accepted first. So approve the ADR before the plan.
>
> 1. **Yes, every project: each one says how its app is started**: The three apps are too different for the runner to guess. Softfield is the dashboard, with no sign-in. Travel-companion (Stampu) is a Django app with its own database of your trips and notes. Coucou is two Django apps whose screens need a paired device. So each project gets a short `[shots]` section in its own settings file: how to make its data, how to start its app, and which address answers once it's up. At the review the runner starts the app twice, on the code from the card's start and on main, takes the pictures and stops it. Any project with that section gets the same Before and after panel on its card pages.
>    Action: ADR 35 items 1–3; f85-01 is rewritten to read `[shots]`, and f85-02 shows any project's pictures.
> 2. **This card sets up Softfield; the other two need a card each**: F85 builds the picture-taking and Softfield's own setting, so Softfield cards get pictures as soon as it's built. Travel-companion's and Coucou's settings live in their own repos, so they're work for their own boards: a small card each, which makes sample data and points the app's database at it. The plant texts are ready to paste on each project's board. Travel-companion: "Set up pictures at sign-off (Softfield ADR 35): a `[shots]` section in .factory/project.toml, a `shots_data` command that builds sample asks, dreams, places and notes from fixtures with no call to the model, and settings that use SOFTFIELD_SHOTS_DATA for the database when it is set." Coucou: "Set up pictures at sign-off (Softfield ADR 35): a `[shots]` section in .factory/project.toml serving the public and admin apps on sample data (a paired sample screen, sample photos that aren't Mum's), with no real data and no back door in the device sign-in." Coucou's card can wait on its board, since product work is on hold. Plant travel-companion's once F85 is built.
>    Action: Plant both cards from each project's own page (the texts are also under 'Other projects' in the card's doc).
> 3. **Your private data stays out of the pictures: sample data for products**: My recommendation: a product is pictured on sample data from its own fixtures, never on its live database. Otherwise Mum's photos and your trip notes would end up in pictures that the review sends to Claude every round. A page might also change something just by loading, or call the model and cost money. The cost: a page that's empty in the sample data looks empty in the picture, and the sample data has to keep up as the app grows. The review says so when it sees an empty page. Softfield is the exception: it's pictured on a copy of the factory's own database, which the review can already read. The alternatives: (b) a copy of the live data, truer pictures but private data in every review; (c) sample data by default, with a per-project switch for a copy of the live data.
>    Action: ADR 35 item 4. Answer only if you prefer (b) or (c).
> 4. **Nothing in your apps can be changed by the pictures**: The app runs on this machine only, on a free local port, just for the pictures. The browser lets through only page loads to that address: no form is sent, and no request goes to another site. A page behind a sign-in (Coucou's screens) is signed in by its sample data, never by a back door added to the product. That matters for Coucou's device sign-in, which is protected code.
>    Action: ADR 35 item 3; f85-01 tests that a form sent from a pictured page reaches nothing.
> 5. **New projects get it at setup**: When `softfield init` sets up a project that has pages, the setup session now also fills in `[shots]` with sample data and takes one picture to prove it works. So a new project shows pictures at its first sign-off, without a card of its own.
>    Action: f85-03 changes the setup guide (docs/bootstrap.md).
> 6. **The first card after setup in a project may have no before**: The before is drawn from the code as it was when the card started, using today's `[shots]` commands. If that old code can't start (say travel-companion's first card after its setup, where the old code doesn't yet know the sample data folder), the panel says 'The page before couldn't be drawn' and still shows the after. It sorts itself out from the next card on.
>    Action: Nothing: covered by D6 on the card.
>
> Proposals:
> - ADR 35: Before and after pictures at sign-off, in every project (adr)
> - F85: real before and after pictures at sign-off, in every project (plan)
> - Before and after on a ripe card's page (mockup)

## The lead, 2026-10-27 14:09

> Each page's address on the Before and after panel is now a link that opens the live page in a new tab. That's in the mock-up, ADR 35, the plan and tickets f85-01 and f85-02. The tickets' checks pass except one, which clears once ADR 35 is accepted, so approve the ADR before the plan.
>
> 1. **Each page's address opens the live page in a new tab**: On every page plate in Before and after, the address (`/board`, `/milestones/f172-i-d-like-to-be-able`) is now a link with a small arrow and the words 'opens the live page in a new tab'. On a Softfield card it opens the dashboard's own page for that project. On a travel-companion or Coucou card it opens your running app, at an optional `live` address in that project's settings (say `http://192.168.1.20:8000`). Bear in mind the link shows the page as it is now, with today's data, while the After picture is main at the review on sample data. So the two can differ, and the link is for poking around rather than for comparing.
>    Action: f85-02 builds the links; f85-01 reads the `live` setting; ADR 35 item 2 adds it.
> 2. **No working address, no link**: A project that hasn't said where its app runs shows the address as plain text, never a link that leads nowhere. The mock-up shows that case on a travel-companion plate. The two plant texts for travel-companion and Coucou now also ask for their `live` address.
>    Action: Nothing more: in the card's D7 and the plant texts under 'Other projects'.
> 3. **Inside the mock-up the links don't open**: The planning room shows a mock-up in a frame that can't open new tabs, so in it the links only look like links. In the built page they open.
>    Action: Nothing.
> 4. **Only addresses on the panel became links**: I took 'sections that have urls' to mean the page plates. The addresses in 'What changed' and 'How to test' are the review's own words and stay text. Linking those means changing how the review writes, which is a separate small card if you want it.
>    Action: Nothing unless you ask; then a small card for the review's text.
>
> Proposals:
> - ADR 35: Before and after pictures at sign-off, in every project (adr)
> - F85: real before and after pictures at sign-off, in every project (plan)
> - Before and after on a ripe card's page (mockup)

## The lead, 2026-10-29 08:14

> Approved by the owner on 2026-10-29: approved plan/f85: queued f85-01-pictures-at-the-review, f85-02-before-and-after-on-the-card, f85-03-planner-lists-the-pages

## The runner, 2026-10-29 22:22

> f85-01-pictures-at-the-review blocked: the lead ticket changed nothing.
> Its work is on task/f85-01-pictures-at-the-review; its run's logs are in .factory/var/runs/20261029-222125/f85-01-pictures-at-the-review.
> What went wrong, and what is the fix? Propose it as a replan: the ticket reworked, split or set aside.

## The lead, 2026-10-29 22:25

> f85-01 stopped without changing anything, and it was right to. Its ADR was never really accepted: three ADRs were numbered 35, and your approval landed on another one that was already Accepted. I've renumbered F85's ADR to 39 and drafted a replan that brings f85-01 back behind a new ticket that fixes the numbering.
>
> 1. **Why f85-01 stopped: your approval reached the wrong ADR**: The ticket starts with 'ADR 35 must be Accepted', and the file it read still said Proposed, so it stopped without changing anything. Three files were numbered 35: 'No backlog file', 'A marked card goes first', and this card's pictures ADR. Your approval this morning ('ADR 35 accepted by the owner', 08:14) brought the pictures ADR onto main. But the runner set the status of the first file numbered 35 in name order, 'A marked card goes first', which was already Accepted, so nothing changed. Both `decide_adr` (runner/owner.py) and `_accept_adr` (runner/requests.py) take the first file with the number. The job cost a few minutes of Claude and nothing else.
>    Action: The replan below.
> 2. **It will happen again on other cards**: Each planner drafts on its own card's branch and takes the next number free on main, so cards planned around the same time pick the same number. Two drafts waiting right now already collide: F127's branch has another 35, and F140's has a 36. Their approvals would go wrong the same way.
>    Action: f85-04 fixes it for every card, below.
> 3. **The pictures ADR becomes ADR 39**: Same text, new number: 39 is free on main and on every branch. The old '35' copy now says it is replaced by ADR 39, and f85-04 removes it. The card's doc and tickets f85-01 and f85-03 now say ADR 39. Please accept ADR 39 first, then approve the replan: the tickets can't be queued while the ADR they need is still Proposed.
>    Action: Accept ADR 39, then approve the replan.
> 4. **New ticket f85-04: an approval always reaches the ADR you approved**: When you approve a draft whose number main already uses, the runner gives it the next free number at that moment, renames it, and updates the card and tickets that mention it. A number that two files on main share is refused, with both files named on your desk, instead of quietly changing the first one. It runs first on this card, and f85-01 waits for it. It's a lead ticket (the runner's code is protected), about one hour of work. The two Accepted ADRs numbered 35 keep their numbers, since other files point at them.
>    Action: f85-04, first in F85.
> 5. **No need to pause the factory**: F85's other tickets are already held behind the blocked one, so none of this card's work can start while you decide. The rest of the line keeps going.
>    Action: Nothing.
>
> Proposals:
> - ADR 39: Before and after pictures at sign-off, in every project (was 35) (adr)
> - F85: renumber its ADR, fix ADR approval, bring f85-01 back (replan)

## The lead, 2026-11-02 19:59

> Approved by the owner on 2026-11-02: approved plan/f85: queued f85-01-pictures-at-the-review

## The lead, 2026-11-02 20:54

> Your Accept reached the wrong ADR twice, the bug this thread found on 29 Oct. It's fixed for every card (an Accept takes the exact file, a taken number moves to the next free one), so f85-04 wasn't needed. This card's ADR is now ADR 40, accepted as you asked, and your approval of 31 Oct was applied: f85-01 is ready again.

## The owner, 2026-11-05 08:13

> The page couldn't be drawn.
> the app didn't answer in 180 s: The factory dashboard: http://127.0.0.1:37697/projects (Ctrl-C stops it)
>
> Why not just a screenshot anyway? Note that I'm on --lan

## The lead, 2026-11-05 08:17

> You're right, it should have just taken the screenshot. I've drafted a replan with one small ticket that makes it do that. Nothing is queued until you approve it.
>
> 1. **Why not just a screenshot? It should have taken one**: Before taking a picture, the runner asks the app's Overview page whether it is up, and gives up on each try after 5 s. The picture itself is allowed 30 s, so the check was far stricter than the thing it was guarding. The Overview took about 4 s when I timed it by hand on the idle machine, and a just-started app is slower. Each abandoned try keeps running inside the app, so the next one is slower still, and it never came back in time. That's the most likely cause: I didn't reproduce the failed run, and the ticket confirms it. F219, Lead tickets follow Claude's week pace, got a Before because that older code answered in time.
>    Action: f85-05: drop the check. Once the app's port takes a connection, take the picture, and only a picture that really fails gives a reason.
> 2. **--lan had nothing to do with it**: The pictures never touch the dashboard you run with --lan. The runner starts its own private copy on this machine, on a spare port, using a copy of the data. The `127.0.0.1:37697` in the message is that copy's start-up line, which is really a sign it was running, not a sign of the fault. No other job was running at the time either, so a busy machine wasn't the reason.
>    Action: f85-05 stops quoting that line: the message will only quote the app when the app stops by itself.
> 3. **If you meant a screenshot of the dashboard you already run: I'd keep the separate copy**: That would work for Softfield's After, but it can't give a Before, because your running dashboard only has today's code. Before and After would also be drawn on different data, so every number would differ as well as the change. For travel-companion and Coucou it would mean pictures of your live data going to Claude, which ADR 40 rules out. The address above each picture already opens the real page when you want to look at it yourself.
>    Action: Nothing: the private copy stays.
> 4. **The fix changes ADR 40 slightly**: The `ready` setting exists only for that check, so it goes. Only Softfield has set up pictures so far, so no other project is affected. I've written this into ADR 40 as an amendment, and approving the replan accepts it. The panel looks the same, so there's no new mock-up.
>    Action: ADR 40's Amendments and D11 on the card.
> 5. **F85 waits for this fix before its sign-off**: Adding the ticket takes F85 off your sign-off list until the fix is built and reviewed: about 40 minutes of lead work plus a review round. It's a lead ticket, so at Claude's week of 81% it may wait behind the week's pace line unless F85 is on the fast lane. I'd still do it this way, because missing pictures are exactly what this card was meant to prevent.
>    Action: Approve the replan. Pull F85's fast lane lever if you want it sooner.
> 6. **You can sign F219 off without its After**: F219's own sheet says the Overview doesn't show its change yet (that comes with f9-29), so the missing After hides nothing. A picture is only taken again if F219 gets another review round. If it doesn't, the message stays on its page until you sign it off.
>    Action: Nothing: F219's sign-off doesn't need to wait.
> 7. **The Overview itself is slow to draw**: About 4 s on an idle machine is a lot for a page you open from your phone. I don't know yet whether it got slower recently. This is a separate job from F85, so here's the text to paste into the Plant box: "The Overview takes about 4 s to draw on an idle machine (timed 2026-11-05): find where the time goes and make it faster, and say whether F219's runner changes made it slower."
>    Action: Plant it if you want it looked at.
>
> Proposals:
> - F85: a slow page still gets its picture (replan)

## The lead, 2026-11-05 09:10

> Approved by the owner on 2026-11-05: approved plan/f85: queued f85-05-fix-slow-page-still-pictured

## The owner, 2026-11-11 12:50

> The screenshots in coaster ranker are lacking css. It doesn't matter too much as it's the very first ticket but that's still concerning. Some older tickets got done with no screenshot. I understand there might not be a before screenshot but there should be at 'east an after screenshot?

## The lead, 2026-11-11 12:56

> I've drafted a replan with three tickets that fix both problems. Nothing is queued until you approve it.
>
> 1. **Why m1's pictures had no styling**: The app coaster-ranker started for the pictures served its pages without their stylesheet. m1's own review saw this, fixed coaster-ranker's picture setup, and wrote 'the next round's pictures will show it'. But m1 (Import both lists, rank Orlando coasters by drag, compare the two) had only one review round, so nothing takes the pictures again before you sign it off. Worse, the factory counted plain unstyled pages as good pictures, and the review compared them with the mock-up. So it's right to be concerned, even though it's the project's first card.
>    Action: f85-06 and f85-08, below.
> 2. **An unstyled page no longer counts as a picture**: While a page loads, the runner watches its stylesheets. If one fails, the picture is marked as not drawn, with the reason, for example 'drawn without its stylesheet: /static/app.css answered 404'. The review no longer compares such a picture with the mock-up. The panel already shows the reason for a failed picture, so the page looks the same and I haven't drawn a mock-up. Ask if you want one.
>    Action: f85-06.
> 3. **A fixed setup shows before you sign off**: The runner now remembers which picture setup and which page list each card's pictures were taken with. At each pick, a card waiting for your sign-off whose setup or list has changed gets new pictures. That costs seconds and no Claude. m1 is the first case: coaster-ranker's setup has changed since its pictures, so if this lands before you sign m1 off, its styled pictures appear by themselves. A picture that simply failed isn't retried on every pick, so a broken setup can't keep starting an app. Fixing the setup is what brings the pictures back.
>    Action: f85-08.
> 4. **No pictures at all: cards whose plan listed no pages**: Pictures are only taken for the pages a card's plan lists, and the planner only started listing them once F85's own tickets were in. So cards planned earlier got none: F61 (the Claude usage page's 'at this rate', signed off today), F9 (Line polish) and F192 (fast lane on the board), and the ones waiting for you now: F77 (allowance bars), F69 (theme switch), F38 (layout shift on refresh) and F193 (project picker). You're right that an After should be there, and in fact a Before can be too: every card keeps a marker of where its work started, so the runner can redraw the page as it was then. From now on, the review lists any changed page the plan forgot, in its first round, and the runner pictures it right after that round. Those four waiting now won't get pictures, because their reviews are over.
>    Action: f85-07.
> 5. **Cost and order**: Three lead tickets, about 30 minutes each at the current median, plus a review round for F85. All three change the runner's own code, which only the lead may change. f85-06 goes first, and 07 and 08 wait for it. F85 sits at priority 11 on the board, behind a long queue. If you want m1's pictures fixed before its sign-off, pull F85's fast lane, or sign m1 off now from the real pages (the address above each picture opens it).
>    Action: Approve the replan; fast lane F85 if you want it sooner.
>
> Proposals:
> - F85: no unstyled pictures, and pictures for every card that changes a page (replan)
