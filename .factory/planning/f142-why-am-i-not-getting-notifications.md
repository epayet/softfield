# F142: Phone notifications: every project, and with the dashboard closed

The planning thread behind F142's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-16 00:08

> Why am I not getting notifications on my phone anymore

## The lead, 2026-10-16 00:12

> I've drafted F142's plan (one ticket) and ADR 31 on the branch. My ticket passes pre-flight. Two older drafts that aren't F142's still fail it: bug-03 waits on ADR 23, and f9-12's files list only tests.
>
> 1. **Most likely cause: notifications follow only the project the page shows**: A dashboard page only notifies for its own project, the one in its ?project=. Since 2026-10-14 (ADR 30, one runner and one dashboard for every project), the dashboard service opens a bare address on the first project in your order. Today that's travel-companion, which has nothing waiting. If your phone's bookmark has no ?project=softfield, it has been watching travel-companion. Softfield did have news: on 2026-10-15 there were two stopped reviews (F19 and F28), two lead replies on F135 (No end-to-end, no stop) and two sign-offs (F109 and F95). None of them could notify a page set to another project.
>    Action: Right now: open the dashboard on the phone, pick softfield in the Project box and keep that page in front. The plan below fixes it for good.
> 2. **On a phone, only an open page in front ever notifies**: This hasn't changed since F12 (Notifications asked once). Chrome freezes a background page within minutes. A page that comes back after more than 60 s also treats what it finds as already known. So anything that arrives while the phone is in your pocket never notifies, even on the right project. If notifications felt more frequent before, you probably had the page open more.
>    Action: Draft ADR 31 (Notifications to a closed phone): see point 4.
> 3. **Fix: one page notifies for every project**: One developer ticket, f142-01. A page on any project also notifies for every other project's waiting items. Their titles start with the project's name ("softfield: The lead replied: …") and a tap opens that project's page. What a browser has already seen becomes one list for the whole dashboard, so switching project neither notifies twice nor misses anything. It builds on F114 (Notifications only for what needs me, already ready) and waits for its second ticket, which rewrites the same script.
>    Action: Ticket f142-01-notify-every-project, queued when you approve.
> 4. **With the dashboard closed: ntfy on the home Wi-Fi (ADR 31)**: Point 3 only helps while a page is open. For a phone in your pocket I recommend the ntfy app with a small ntfy server on this machine. The always-on dashboard service would send it the same notifications the page shows, and the phone shows them with the screen off. The cost is a new always-on service you install yourself, a little battery for the app, and nothing reaching you away from home. The other choices: the public ntfy.sh (nothing to install and works anywhere, but card titles go to a third party, which goes against your 'home Wi-Fi only' rule), or nothing.
>    Action: Answer the ADR's question 1 (A: this machine, recommended; B: ntfy.sh; C: nothing). Its two tickets come once you accept it.
> 5. **If even an open Softfield page stays silent**: Then it's the address, not the code. Chrome only notifies on an address it was told to trust (ADR 26: chrome://flags, 'Insecure origins treated as secure'). The setting is lost if this machine's LAN address changes, or sometimes after a Chrome update. The prompt bar only shows once per address, so it won't remind you.
>    Action: On the phone, check that the flag still lists the address in the dashboard's top bar, and that Chrome's site settings for it allow notifications. Tell me here if either is off. A fixed address for this machine in the router stops it from happening again.
> 6. **No mock-up**: No page changes. Only the notifications' own words change (the project's name before the title).
>    Action: Nothing.
>
> Proposals:
> - F142: notify for every project (plan)
> - ADR 31: Notifications to a closed phone, through ntfy on the home Wi-Fi (adr)

## The owner, 2026-10-16 09:23

> explaint what ntfy is, if it's time to use docker for this and what it's the ideal solution here

## The lead, 2026-10-16 09:27

> I've answered your three questions and revised ADR 31: I now recommend a nudge through the public ntfy.sh over running our own server, so nothing gets installed and Docker isn't needed. F142's own plan hasn't changed.
>
> 1. **What ntfy is**: ntfy is a free, open-source notification service. A program sends a message with one web request to an address like https://ntfy.sh/some-secret-word. The ntfy app on your phone listens to that same 'topic' word and shows the message right away, with the screen off and no browser open, like a text message. You can use the public server, ntfy.sh, which ntfy's author runs for free, or run your own copy. The difference matters on the phone. The Play Store app gets ntfy.sh's messages through Google's normal push channel, like any other app, so it costs no battery of its own. A server of your own has no such channel, so the app keeps a connection open to it all day. That costs battery, and it only works where the phone can reach the server: on the home Wi-Fi.
>    Action: Nothing.
> 2. **Docker: not yet, and not for this**: Nothing here uses Docker today: the runner and the dashboard are plain systemd user services. Docker would add a background service that runs with root rights, network port mappings and image updates to look after, all to run one small program. Our own ntfy server would be a single program you can install directly, and with the recommendation below there's no server to run at all. Docker becomes worth it when several services have clashing dependencies, or when the factory has to move to another machine in one piece (the 'software factory' of ADR 02). That's a separate decision for later.
>    Action: ADR 31 item 5: no Docker.
> 3. **The ideal solution: a nudge through ntfy.sh, not our own server**: I've changed my recommendation from last time. The best setup sends the public ntfy.sh only 'Softfield: 2 things need you', never a card title or a reply. Tapping it opens the dashboard, where the details live and which stays on the home Wi-Fi. That means nothing to install or run, it reaches you anywhere, and it costs no battery. ntfy.sh learns only when the factory needs you and how many things are waiting. The trade-off: the lock screen won't say which card it's about. Running our own server would get the titles on screen, but costs a new always-on service, battery all day, and nothing when you're away from home. I'd only move to that if the nudge turns out too vague. Sending full titles through ntfy.sh gives the best messages, but every card title would go to a third party in plain text, which I don't recommend.
>    Action: Answer ADR 31's question 1: A (ntfy.sh, nudge only, recommended), B (our own server, full titles), C (ntfy.sh with full titles) or D (nothing).
> 4. **What ADR 31's choice doesn't change**: The ticket that makes one page notify for every project (f142-01, waiting for F114, Notifications only for what needs me) stands whichever option you pick. The nudge counts every project's waiting items the same way.
>    Action: Nothing.
>
> Proposals:
> - F142: notify for every project (plan)
> - ADR 31: Notifications to a closed phone, through ntfy (adr)

## The owner, 2026-10-16 20:39

> I sent back your proposal “ADR 31: Notifications to a closed phone, through ntfy” (adr-31).
> - On its key point 2 (A nudge through the public ntfy.sh): why not 1 notification per thing i need to do, which will also open the right page (review, answer to my question). Is it because it's public, and some notifications could be batched?
> - On its key point 3 (The dashboard service sends it): why that versus sending a notification/event from the thing itself, like when a proposal group is created, it sends the notification right now? rather than an infinite loop
> - On its key point 4 (The topic is the key): why not in the repo factory config?
> - On its key point 8 (Your choice: where messages go): i'm happy with free ntfy.sh to begin with, it has 250 free messages per month i believe. i'll need instructions on how to install and use the app on my phone when you're done

## The owner, 2026-10-16 20:39

> i've sent back the adr with more thoughts, here's another one: this shouldn't remove the notification existing on web btw, it should do both and clients can decide which one they want to use (block browser notifications, may decide to use ntfy). the code that sends a notification colud be able to do both,  like notify('thing') sends to both browser and ntfy

## The lead, 2026-10-16 20:42

> I revised ADR 31 along your four comments: one notification per thing, sent by the runner the moment it happens, with the topic kept in the machine's settings. I also added two tickets to F142's plan. The plan can only be approved once you've accepted ADR 31.
>
> 1. **One notification per thing, opening its page: yes**: Agreed, and the ADR now says so. I'd only cut it to a nudge to keep card titles away from a public server, and that works per item too. Each notification gives the kind of thing and the project: 'softfield · The lead answered you', 'A card is ready for your sign-off', 'A review stopped', 'A ticket needs your decision'. A tap opens the page where you act: the card's thread for an answer, a sign-off or a stopped review, the Overview for the rest. It still never carries the card's title or the reply's text, because ntfy.sh is public. One exception to one-per-item: a review can raise two or three items about the same card in the same second, and those come as one ('3 things need you on one card') rather than three buzzes. The page only opens on the home Wi-Fi, like the dashboard.
>    Action: ADR 31 items 1 and 2.
> 2. **Sent by the runner when it happens: you're right**: Your way is better. I had picked the dashboard because it already words the browser's notifications. But every item that needs you is stored by the runner, in only three places: a review's verdict, a lead's reply and Claude's reserve switch going off. Sending right there is instant, needs no loop and no memory of what was already sent, and can't send twice when the dashboard restarts. The cost: two things the dashboard alone notices won't reach the phone, a runner that died mid-job (a dead runner can't send, and systemd restarts it) and tickets waiting with no runner. Sending is best-effort: if ntfy.sh is down, the run's report gets one line and the job carries on.
>    Action: ADR 31 item 3; ticket f142-02 (mine: a request leaving the machine).
> 3. **Why the topic isn't in the repo's config**: Two reasons. First, the topic is the only lock: anyone who reads it can read your notifications and send you fake ones. The repo is pushed and shared with every agent and every job's log, which is not true of a file in your home folder. Second, since ADR 30 the runner and its notifications belong to the machine, not to one project: the repo config would need the topic in every project, and the next project you set up would arrive silent. The machine's ~/.config/softfield/factory.toml already holds the machine-wide settings (the roles), so the topic goes there. You won't edit it by hand: `softfield notify setup` writes it once.
>    Action: ADR 31 item 4.
> 4. **ntfy.sh's free limit**: You chose free ntfy.sh, and that's now in the ADR. I believe its free limit is about 250 messages a day rather than a month, but I can't check from here; ntfy.sh's pricing page has the exact numbers. Either way it's enough: the busiest day so far raised about twenty items (2026-10-13), and a normal day is under ten. If a limit is ever hit, the rest of that day's notifications are lost, the desk still holds everything, and moving to a server of our own changes only one address.
>    Action: Nothing.
> 5. **Phone instructions: ticket f142-03, preview here**: Ticket f142-03 writes them to docs/notifications-on-the-phone.md. The commands exist once f142-02 has merged. 1) On this computer run `softfield notify setup` once; it prints your topic. 2) On the phone install 'ntfy' from the Play Store and open it. 3) Tap +, type the topic, leave 'Use another server' off, tap Subscribe, and allow notifications when Android asks. 4) Back on the computer run `softfield notify test`; 'softfield · Notifications work' should appear on the phone. 5) In Chrome on the phone, turn off the dashboard's own notifications (site settings), so nothing comes twice. `softfield doctor` will also say whether it's set up.
>    Action: Ticket f142-03 (developer); I'll point you to the doc when it lands.
> 6. **Order: accept the ADR, then approve the plan**: Tickets 02 and 03 rely on ADR 31, so Approve refuses the plan while the ADR is still Proposed. f142-01 (every project on the open page) waits on it too, since it's in the same plan; it would have waited for F114 anyway.
>    Action: Accept ADR 31, then approve the plan, both on this page.
>
> Proposals:
> - ADR 31: Notifications to a closed phone, through ntfy (adr)
> - F142: notify for every project, and on a closed phone (plan)

## The lead, 2026-10-16 20:46

> I've reworked ADR 31 and the plan around one `notify` call that feeds both the browser and the ntfy app. Pre-flight's only complaint is the expected one: all three tickets wait for ADR 31 to be accepted.
>
> 1. **Both channels, from one notify: yes, with one limit**: Agreed: browser notifications stay, ntfy comes on top, and each device chooses. You can block the dashboard in Chrome, or simply not install the app. One limit: the server can't push to a browser. Without https (which you turned down in ADR 26), a browser only hears from the dashboard when its page asks every 5 s. So notify('thing') can't literally deliver to Chrome. Here is the design that gets the same effect. notify() in runner/notify.py stores the notification once, as a row in a new notifications table, then sends it to ntfy. Every open dashboard page shows the rows it hasn't shown yet. That makes one decision, one moment and one set of words for both channels, with nothing else deciding what notifies.
>    Action: ADR 31 item 4.
> 2. **What the shared record improves on the browser too**: Today a page that comes back from sleep after more than 60 s silently drops what came in meanwhile. With the rows, it shows what it missed as one notification ('3 things need you'), opening the desk. Notifications from every project come too, with the project's name in front (the cause from your first message). One difference between the channels is deliberate: the browser's notification names the card, ntfy's never does, because ntfy.sh is public.
>    Action: Ticket f142-01 (developer) now has the browser read the rows.
> 3. **Cost: part of F114 gets reworked**: F114 (Notifications only for what needs me) is ready and lands first as planned. Its tap that opens the right page is kept as it is. But the notification wording it builds in the dashboard moves into runner/notify.py, and its 'compare open items every 5 s' step is replaced by reading the rows. That's about half of F114's second ticket redone, on the local model. I'd rather pay that than keep two ways of deciding what notifies, which would drift apart. The other option is to replan F114 first so it never builds the part that moves. That means a message on F114's thread and holding F114 back. I don't recommend it: F114 is small and runs on the local model.
>    Action: Nothing, unless you'd rather replan F114 first: say so here.
> 4. **What the browser keeps checking on its own**: Two things only the dashboard can see: a runner that stopped mid-job (a dead runner can't send anything) and tickets waiting with no runner. Those stay as the page's own check, browser only. 'All work done' becomes a notify() from the runner, so the phone gets it too.
>    Action: ADR 31 item 4.
> 5. **Your earlier comments are in**: One notification per thing, opening its page; sent from where it happens rather than by a loop; ntfy.sh free to begin with; the topic kept outside the repo, for the reasons I gave. They're listed under 'Settled with the owner' in the ADR. I took the comments you sent back with the ADR to be the four I answered last time. If anything else was meant to come with them, it didn't reach this thread: send it again here.
>    Action: Nothing.
> 6. **Order: accept the ADR, then approve the plan**: All three tickets rely on ADR 31, so Approve refuses the plan until it's accepted. They run in this order: f142-02 (mine: notify, its table, the ntfy send, the setup and test commands), then f142-01 (the browser shows the rows, once F114 has landed) and f142-03 (your phone instructions and a check in softfield doctor).
>    Action: Accept ADR 31, then approve the plan, both on this page.
>
> Proposals:
> - ADR 31: Notifications to a closed phone, through ntfy (adr)
> - F142: one notify for the browser and the phone, every project (plan)

## The owner, 2026-10-17 00:17

> Why is the plan adding a notification table, this seems unnecessary it just needs to send it straight away why store it

## The lead, 2026-10-19 23:20

> You're right: there's no notifications table. The plan's three tickets pass pre-flight and wait only for your Approve. I've recorded the change in ADR 31, which you accepted on 2026-10-16.
>
> 1. **No table: you're right**: The table was there only for the browser. A browser can't be sent anything (that would need https, which ADR 26 turned down). It only hears from the dashboard when its page asks every 5 s, so I wanted something to hold the notification until the page asked. But something already holds it: the item the runner stores for you, the one that puts a reply or a sign-off on your desk. Since my last reply F114 (Notifications only for what needs me) has landed, and the browser already notifies from those stored items. A second table would only copy them. So the runner sends to ntfy the moment it stores the item, and stores nothing more. The browser notices the same item on its next look. Both come from the same moment and the same record, which was the point of your 'both channels' note.
>    Action: ADR 31 item 4 amended at your word, the table dropped from f142-02, no new database table.
> 2. **What dropping the table gives up**: One small thing: a browser page that comes back from sleep still won't show what came in while it slept, as today. The rows would have let it catch up. I don't think that's worth a table: the phone gets everything through ntfy, and the desk holds the rest.
>    Action: Nothing.
> 3. **f142-01 back to its first form, on F114 as built**: With no rows to read, f142-01 goes back to what it was first: an open page notifies for every project's items, with the project's name in front, and remembers one list of what it has seen for the whole dashboard. It now starts from the code F114 left and waits for F114's three fix tickets still in the queue (f114-07, 08 and 09), which change the same script and tests.
>    Action: Ticket f142-01 (developer, difficulty 3).
> 4. **Ready to approve**: ADR 31 is accepted, so all three tickets pass pre-flight. f142-02 (mine: the ntfy send and the setup and test commands) can start at once. f142-03, your phone instructions, follows it.
>    Action: Approve the plan on this page.
>
> Proposals:
> - ADR 31: item 4 amended, no table of notifications (adr)
> - F142: notify for every project, and on a closed phone (plan)
