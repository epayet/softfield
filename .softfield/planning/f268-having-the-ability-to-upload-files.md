# F268: Add pictures to a plant or a thread message

The planning thread behind F268's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-18 07:38

> Having the ability to upload files in conversations would be helpful. For planting ideas too. Like a screenshot to show what I mean sometimes

## The lead, 2026-11-18 07:42

> I've drafted the plan for F268: an ADR, a mock-up and four tickets. Pictures only (screenshots and photos), added from the Plant box and a thread's reply box.
>
> 1. **Pictures only, no other files**: Your example is a screenshot, so I've planned for pictures only: screenshots and photos, up to 6 per plant or message. Text and logs are easier to paste than to upload, and nothing so far has needed a PDF. Allowing any file would also mean checking more file types, and the local models can't open most of them.
>    Action: ADR 49 item 1. If you do want PDFs or other files, say so and I'll add them.
> 2. **The phone shrinks the picture before sending it**: A 3 MB phone screenshot is shrunk on the phone to at most 1600 px on its longest side, so it arrives at about 200–400 KB. Text stays readable for the lead, sending is quick on the Wi-Fi, and the repo grows by about 300 KB per picture. The shrinking happens in the browser, so the factory needs no new Python package.
>    Action: ADR 49 item 2; ticket f268-03.
> 3. **A new kind of dashboard write: your decision**: Today the dashboard's only write is a request row (ADR 18, The dashboard on the home Wi-Fi). I recommend the pictures go in the same send as your words, stored in a new table next to that row, behind the same check that the send comes from the dashboard's own page. Only PNG and JPEG are taken, checked by their contents rather than their name, so a disguised script can't get in, and each is capped at 2 MB. The daily Dropbox copy covers them with your words. Turned down: a separate upload step, which leaves orphan files when you never send the message, and having the dashboard write files on disk itself.
>    Action: Accept ADR 49 from its page if you agree. The tickets can't be queued until it's accepted.
> 4. **Where the pictures end up**: They show straight away on the waiting plant or message, with the dashed orange edge, and a tap opens one full size. At its next pick the runner commits them to the card's folder in git (`.softfield/cards/<card>-files/`), and a planted card's notes show them. A message on the general thread keeps them in the database only, because it has no card folder.
>    Action: Tickets f268-02 and f268-04.
> 5. **The lead looks at them**: When a message has pictures, the planner's prompt lists their paths and tells it to open each one before answering. The lead runs on Claude, which can read images. A ticket can point at a picture too, but the local developers can't be relied on to see it.
>    Action: Ticket f268-02.
> 6. **The mock-up**: It shows the Plant box and a thread's reply box, Today and Proposed: an 'Add a picture' button (your phone's photos or camera), thumbnails with a ✕ to remove one, and on a wide screen you can paste or drop a picture too. Your waiting message shows its picture straight away.
>    Action: Read .softfield/cards/f268-mockup/pictures.html. Ticket f268-03 builds from it.
> 7. **Who builds it, and when**: There are four tickets. Three are for the lead, because they touch the dashboard's one write route and the runner, and the picture box is a new kind of browser code. The fourth is for a developer: showing thumbnails on waiting items. That's about 3 hours of work. Approving puts F268 at the end of the board, behind 60 ready cards. Drag it up if you want it sooner.
>    Action: Approve the plan once ADR 49 is accepted.
>
> Proposals:
> - ADR 49: Pictures with the owner's words (adr)
> - Pictures in the Plant box and on a thread (mockup)
> - F268, pictures with a plant or a message: 4 tickets (plan)

## The owner, 2026-11-18 07:59

> On point 1: Let's do other files. This is meant for the lead only usually
> On point 2: no changing of the original file

## The lead, 2026-11-18 08:02

> I've reworked F268 for any file, kept exactly as you pick it. Files no longer go in git: they stay out of the repo, with a second copy in Dropbox.
>
> 1. **Any file, not just pictures**: Agreed: screenshots, photos, PDFs, logs, anything, up to 6 per plant or message. The lead can open pictures, PDFs and text files. For anything else (a zip, a Word file, an iPhone HEIC photo) it gets the file's path and says in a point that it couldn't open it, so a file never goes unnoticed.
>    Action: ADR 49 item 1; tickets f268-01 to f268-04 reworked.
> 2. **The original file, unchanged**: Agreed: no shrinking. The lead gets the exact bytes you picked, and a test checks that. The cost: a phone photo is 3–8 MB, so it takes a few seconds to send over the Wi-Fi. I've capped each file at 25 MB so one huge video can't fill the disk. A bigger file is refused in the box straight away, with the reason, before anything is sent.
>    Action: ADR 49 item 1; ticket f268-03.
> 3. **Changed from the first draft: files stay out of git**: Since the files are mostly for the lead and kept at full size, putting them in git would keep every photo and PDF in the repo's history forever. Keeping them only in the metrics database is no better: 14 daily copies of it are kept in Dropbox, so each file would be stored 14 times. So the database holds a file only until the runner's next pick. The runner then writes it to the project's `.softfield/var/files/` (outside git), puts one copy in the Dropbox backup folder, and clears it from the database. That leaves two copies: one on this machine, one in Dropbox. A planted card's notes list each file with its path.
>    Action: ADR 49 items 3 and 5; ticket f268-02.
> 4. **Any file, opened safely**: Accepting any file means a page or a script could be sent too. The dashboard shows only PNG, JPEG, GIF and WebP pictures directly, recognised by their contents rather than their name. Everything else, including SVG and HTML, downloads instead of opening. That way nothing inside a file can run in the dashboard.
>    Action: ADR 49 item 4; ticket f268-01.
> 5. **The mock-up, updated**: The button now says 'Add a file' and opens your phone's photos, camera or files. A picture still shows as a thumbnail; any other file shows as a tile with its name and size. The sizes shown are the original sizes. The waiting message on the thread shows a picture and a log file.
>    Action: Read .softfield/cards/f268-mockup/pictures.html. Tickets f268-03 and f268-04 build from it.
> 6. **Order and timing unchanged**: The same four tickets, about 3 hours of work: three for the lead, one for a developer. The tickets can't be queued until ADR 49 is accepted, so accept it first, then approve the plan. F268 then joins the end of the board; drag it up if you want it sooner.
>    Action: Accept ADR 49, then approve the plan.
>
> Proposals:
> - ADR 49: Files with the owner's words (adr)
> - Files in the Plant box and on a thread (mockup)
> - F268, files with a plant or a message: 4 tickets (plan)
