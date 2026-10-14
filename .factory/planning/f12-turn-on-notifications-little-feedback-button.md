# F12: Turn on notifications  little feedback button

The planning thread behind F12's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-07 21:11

> Turn on notifications  little feedback button
>
> The button on mobile is on the left rather than right. Also, what is it supposed to do? Do we even need it and just send notifications by default?

## The lead, 2026-10-07 21:11

> Answered from the code and the queue as they stand today. Reply on any point; every point you don't comment on counts as agreed.
>
> 1. **What it does**: It asks your browser once for permission. Then, while a dashboard page is open, it pops a notification when something new needs you, and once when all the work is done. Nothing comes once every dashboard page is closed.
>    Action: Nothing
> 2. **It does nothing on your phone**: Chrome on Android only shows notifications sent through a service worker, and the dashboard has none: the page tries, the browser refuses, and the error is swallowed (notify.js). So on the phone the button is a dead end today. Recommendation: a tiny service worker that only shows notifications (no push), so it works on the phone too while a page is open.
>    Action: A ticket: notifications through a service worker, so they show on Android
> 3. **Why not on by default**: A page can't grant itself notifications: the browser must ask you once, after a tap. Once you say yes it stays on for that browser and the button hides. So the button stays, but only until you've said yes.
>    Action: Nothing
> 4. **Left instead of right on mobile**: A layout slip in the top bar's phone layout. It goes in the same ticket: on the phone the button sits on the right, and hides once allowed.
>    Action: In the ticket of point 2
> 5. **Notifications with the dashboard closed**: That is web push (a service worker plus a push subscription over https). It is in the roadmap, not planned. Worth an ADR only if point 2 isn't enough for you.
>    Action: Nothing for now; the roadmap

## The owner, 2026-10-07 23:08

> On point 1: well, when i click on it, nothing happens right now even on desktop
> On point 2: this might not be a problem only on android
> On point 3: what happens if there is no 'turn on notifications' button and it tries to send a notification while i'm not focused on the page, is this what the button is trying to solve? for me to say yes while i'm there? how about asking when the page loads for the first time for me to say yes (not every single time though especially if i said no). check what's common to do for other websites, keeping it mind that this is my own factory so keep it simple for now

## The lead, 2026-10-07 23:10

> You were right on both counts. The button can't work on the address you use, on any device. I've drafted a fix: the dashboard asks once, on your first visit, and the top bar button goes.
>
> 1. **Why nothing happens on desktop.** You open the dashboard at its home Wi‑Fi address over plain http. Browsers only allow notifications on a secure address: https, or 127.0.0.1 on the same computer. So `notify.js` greys the button out, and the only explanation is a tooltip that appears when you hover the mouse over it. Clicking a greyed-out button does nothing, and a phone can't hover, so you never saw why. When we built the button (f5-12) it was only tested on 127.0.0.1, which is how this slipped through.
>    *Action:* ADR 26 item 1: give the dashboard a secure address. Open question 1 below.
>
> 2. **Not only an Android problem.** Correct. The insecure address blocks every browser. Android adds a second block on top: Chrome there only shows notifications through a service worker (a small background script the browser keeps for the site).
>    *Action:* ADR 26 item 3 and ticket f12-01: a small service worker that only shows notifications.
>
> 3. **What the button solves, and asking on first load.** Yes, the button is how you say yes while you're there. Without your yes, the page can't send any notification, focused or not. Most sites now do what you suggest, with one detail: they first show their own small question ("Get notified? Yes / Not now"), and only after you tap Yes does the browser's own prompt appear. Asking straight away on load doesn't work well: Firefox and Safari ignore a prompt you didn't tap for, and Chrome hides prompts from sites that ask on load.
>    So I propose: on your first visit, a small bar under the top bar asks once. Yes brings up the browser's prompt. "No thanks" is remembered in that browser and never asked again. You can still change your mind later in the browser's site settings. The top bar button goes.
>    *Action:* ADR 26 item 2 and ticket f12-01.
>
> 4. **The button on the left on the phone.** The phone layout of the top bar pins it left (`justify-self: start`, `dashboard.css:262`). The button goes entirely (point 3), so there's nothing left to move.
>    *Action:* in f12-01.
>
> 5. **A limit on the phone you should know about.** Even once this works, a phone pauses a page in the background after a few minutes. So the phone notifies while the dashboard is open or was just left, not hours later with the screen off. Getting notifications with the page closed needs web push. That's still in the roadmap. If you want it, it needs ADR 26 option B or C rather than A.
>    *Action:* nothing now; the roadmap.
>
> 6. **How to get the secure address (your one decision).** I recommend **A**: tell Chrome on your desktop and your phone to trust the dashboard's address. Open `chrome://flags/#unsafely-treat-insecure-origin-as-secure`, add the address, relaunch. That's two minutes per device and no code.
>    - The downsides: it's per browser, you redo it if the machine's home address changes (a fixed address in the router avoids that), and Chrome could drop the setting one day.
>    - **B** is real https with your own certificate (`mkcert`): you install a certificate once on each device. It needs a code change, and it puts a root key on the machine that could fake any website on your devices if it were stolen.
>    - **C** is Tailscale: a real certificate with nothing to install except the Tailscale app. But you chose the home Wi‑Fi without Tailscale on 2026‑10‑02, so I've flagged it.
>    *Action:* ADR 26 open question 1.
>
> 7. **Repeats.** None. I checked F13 to F26 and the ready cards: none is about notifications.
>    *Action:* nothing.
>
> The ticket is in `tasks/later/`, not ready, so the factory can't pick it up while we talk and you don't need to pause it. Once you answer point 6, I'll put your answer into the ADR. After that, `uv run runner accept 26` accepts it.
>
> Next session: `claude --model sonnet "F12: fold the owner's answer into ADR 26, then queue f12-01"`
>
> 1. **Why nothing happens on desktop**: You open the dashboard at its home Wi-Fi address over http. Browsers allow notifications only on a secure address (https or 127.0.0.1), so the button is greyed out and the reason only shows on mouse hover. f5-12 was only tested on 127.0.0.1.
>    Action: ADR 26 item 1: give the dashboard a secure address
> 2. **Not only an Android problem**: Correct: the insecure address blocks every browser. Android also needs a service worker to show any notification.
>    Action: ADR 26 item 3 and ticket f12-01: a service worker that only shows notifications
> 3. **Ask on the first visit instead of a button**: Without your yes the page can't notify at all, so something has to ask. Common practice is the site's own small question first, then the browser's prompt after a tap (Firefox and Safari ignore prompts on load). So: a bar on your first visit, Yes or No thanks, remembered and never asked again. The top bar button goes.
>    Action: ADR 26 item 2 and ticket f12-01
> 4. **Button on the left on the phone**: The phone layout pins it left (dashboard.css:262). The button goes, so this goes with it.
>    Action: In f12-01
> 5. **The phone notifies only while the page is open or just left**: Phones pause background pages after a few minutes. Notifications with the page closed need web push, which is still in the roadmap and would want ADR 26 option B or C.
>    Action: Nothing now; the roadmap
> 6. **How to get a secure address**: Recommended A: trust the address in Chrome on the desktop and the phone (one setting, two minutes, no code). B: your own https certificate (mkcert), robust but needs code and a root key to protect. C: Tailscale, which you ruled out on 2026-10-02.
>    Action: ADR 26 open question 1: your choice
> 7. **Repeats**: None: no other card or thread is about notifications.
>    Action: Nothing
>
> Proposals:
> - ADR 26: Notifications that work on the home Wi-Fi (adr)
> - F12: notifications that really arrive, asked once (plan)

## The owner, 2026-10-07 23:17

> On point 1: i use with --lan, will it never be possible to have notifications at all with my ip address?
> On point 6: same question, is that truly the only way

## The lead, 2026-10-07 23:33

> Yes, you can keep `--lan` and your IP address. What fails is the plain http, not the IP. I've updated ADR 26 to list every way I know of, including one that needs no secure address at all.
>
> 1. **Notifications with your IP address.** It's possible. Browsers never allow notifications on a plain http address, whatever the address is. But both A and B keep your IP:
>    - **A** doesn't change the address. It tells Chrome to treat that one address, `http://<your IP>:<port>`, as secure.
>    - **B** gives you `https://<your IP>:<port>`. mkcert can make a certificate for an IP address, not only for a name.
>    - Only C changes the address, to a Tailscale one.
>    *Action:* ADR 26 open question 1 now says so.
>
> 2. **Is that truly the only way?** For browser notifications, A, B and C are the only ways that work.
>    - **Two options I ruled out:**
>      - A self-signed certificate that you click through ("Proceed anyway"): browsers still block the service worker on such a page, so the phone wouldn't work.
>      - Also listening on 127.0.0.1: that only helps a browser on the factory machine itself, and it opens one more address to listen on.
>    - **One real alternative that isn't a browser notification:** the **ntfy** app on your phone. A small ntfy server runs on this machine, at your IP over plain http, with no certificate. The runner sends it a message when something needs you. Your phone then shows it even with the dashboard closed and the screen off. In-browser notifications can't do that (point 5 of my last reply).
>    - **ntfy's cost:** one more always-on service on the machine, and an app on the phone.
>    - **My recommendation:** do F12 with A now, two minutes per device and no code, so the dashboard works while it's open. Keep ntfy as the next step for when you want alerts with the dashboard closed. ntfy no longer depends on B or C, so it's the simpler path for that.
>    *Action:* ADR 26 Consequences and F12's "Not in this milestone" now describe ntfy; it becomes a separate card when you want it.
>
> 3. **Repeats.** None. F27 to F30 are about pausing, the top bar and conversations. No card or thread mentions notifications.
>    *Action:* nothing.
>
> The ticket is still in `tasks/later/`, so there's no need to pause the factory. To go ahead, just reply "A" (or B or C), or say if you'd rather start with ntfy. I'll then put your answer into the ADR, and after that `uv run runner accept 26` accepts it.
>
> 1. **Notifications with your IP address**: Possible. The plain http blocks notifications, not the IP. A keeps http://<IP>:<port> and tells Chrome to trust it; B serves https://<IP>:<port> with a certificate made for the IP. Only C changes the address.
>    Action: ADR 26 open question 1 now says A and B keep your --lan address
> 2. **Is that truly the only way**: For browser notifications, A, B and C are the only ways that work. A clicked-through self-signed certificate doesn't fix the phone, and also listening on 127.0.0.1 only helps the factory machine itself. Outside the browser: the ntfy app with a small ntfy server on this machine works over plain http at your IP, even with the dashboard closed. It costs one more service and an app. Recommendation: A now for F12, ntfy later for alerts with the dashboard closed.
>    Action: ADR 26 Consequences and F12's 'Not in this milestone' name ntfy as the next step; a separate card when you want it
> 3. **Repeats**: None: no other card or thread is about notifications.
>    Action: Nothing
>
> Proposals:
> - ADR 26: Notifications that work on the home Wi-Fi (adr)
> - F12: notifications that really arrive, asked once (plan)

## The owner, 2026-10-08 08:51

> I sent back your proposal “ADR 26: Notifications that work on the home Wi-Fi” (adr-26).
> - On its key point 2 (A secure address, keeping --lan and its IP): a

## The lead, 2026-10-08 08:57

> I've written your choice of A into ADR 26: Chrome on each device is told to trust the dashboard's address, which keeps `--lan`, your IP and plain http, with no code change. No other card or thread is about notifications.
>
> 1. **Option A is now settled in the ADR.** Item 1 now holds the setup steps, and a new "Settled with the owner" section records your choice and the costs you accepted:
>    - you redo the setting if the machine's address changes;
>    - Chrome may drop the setting one day, and https with your own certificate (option B) is the fallback then.
>
>    The other options stay in the ADR as the ones you weighed.
>    *Action:* ADR 26 is ready to accept.
>
> 2. **The setup is yours to do, on both devices.** In Chrome on the desktop and on the phone:
>    1. Open `chrome://flags/#unsafely-treat-insecure-origin-as-secure`.
>    2. Add `http://<your IP>:<port>` (the address you open now).
>    3. Relaunch.
>
>    One thing to watch: if the router hands this machine a new address, notifications stop silently. A fixed address for this machine in your router's settings avoids that.
>    *Action:* do it whenever you like; the real-device check at sign-off confirms it.
>
> 3. **A small change to the ticket.** f12-01's bar, on an address not yet trusted, now spells out the setting to change and fills in the page's own address. You won't need to come back to the ADR to find the steps.
>    *Action:* f12-01 edited (it's still in `tasks/later/`).
>
> 4. **Pausing the factory.** Not needed: f12-01 isn't in the ready queue, so nothing can start on it before you approve.
>    *Action:* nothing.
>
> 5. **Repeats.** None. I checked F31 to F50 too.
>    *Action:* nothing.
>
> To accept the ADR: `uv run runner accept 26`. Then approve the F12 plan from the dashboard to queue f12-01.
>
> Next session: `claude --model sonnet "F12: queue f12-01 once ADR 26 is accepted"`
>
> 1. **Option A is now settled in the ADR**: Each Chrome trusts http://<your IP>:<port>; --lan and plain http stay. Recorded under 'Settled with the owner', with the costs you accepted and option B as the fallback.
>    Action: ADR 26 ready: uv run runner accept 26
> 2. **The setup is yours to do, on both devices**: chrome://flags/#unsafely-treat-insecure-origin-as-secure, add the dashboard's address, relaunch, on the desktop and the phone. A fixed address for the machine in your router keeps it working.
>    Action: Your one-time setting; checked at sign-off
> 3. **A small change to the ticket**: On an untrusted address, the bar now spells out the setting to change and fills in the page's own address.
>    Action: f12-01 edited, still in tasks/later
> 4. **Pausing the factory**: Not needed: f12-01 isn't in the ready queue.
>    Action: Nothing
> 5. **Repeats**: None, F31 to F50 included.
>    Action: Nothing
>
> Proposals:
> - ADR 26: Notifications that work on the home Wi-Fi (adr)
> - F12: notifications that really arrive, asked once (plan)

## The owner, 2026-10-08 13:04

> I sent back your proposal “F12: notifications that really arrive, asked once” (f12-plan).
> - On its key point 1 (Done when): how will this work? how will chrome trust? is this something asked for the user to say yes?

## The lead, 2026-10-08 13:10

> Chrome won't ask to trust the address. You change one hidden Chrome setting yourself, once on each device. After that, the dashboard asks you once, and you say yes twice: once in the dashboard's bar, once in Chrome's usual "Allow notifications?" prompt.
>
> 1. **How Chrome comes to trust the address.** Chrome never offers this; it's a setting you change by hand. On the desktop and on the phone:
>    1. Type `chrome://flags/#unsafely-treat-insecure-origin-as-secure` in the address bar.
>    2. In the box on that page, write the dashboard's address, the one you open today, for example `http://192.168.1.20:8765`.
>    3. Set it to Enabled and tap Relaunch.
>
>    It takes two minutes. Chrome then treats that one address as secure, and nothing else changes.
>    *Action:* the F12 card now has a "How it works for you" section with these steps.
>
> 2. **What you'll see after that.**
>    - On your next visit, a bar under the top bar asks: "Get a notification when something needs you, or when all the work is done? Yes / No thanks".
>    - Tap Yes, and Chrome shows its own small "Allow notifications?" prompt. Tap Allow.
>    - The bar never comes back in that browser.
>    - From then on, notifications pop up while a dashboard page is open; on the phone, also for a few minutes after you leave it.
>    - If you skipped step 1, the bar instead says this address can't show notifications yet, with the same steps.
>
>    *Action:* in the card's "How it works for you". f12-01 already builds the bar this way, so the ticket is unchanged.
>
> 3. **Done when, reworded.** The first item now reads as what it is: the ticket merged. The Chrome setting is a step you do on your desktop and your phone, so it comes second. A test notification on both devices closes it at sign-off.
>    *Action:* F12's Done when edited.
>
> 4. **Repeats.** None: F51 to F58 don't touch notifications.
>    *Action:* nothing.
>
> ADR 26 is unchanged and ready to accept: `uv run runner accept 26`. Then approve the F12 plan from the dashboard.
>
> 1. **How Chrome comes to trust the address**: Chrome never offers this; you change a setting by hand, once per device: chrome://flags/#unsafely-treat-insecure-origin-as-secure, write the dashboard's address (e.g. http://192.168.1.20:8765), Enabled, Relaunch.
>    Action: F12 card: new 'How it works for you' section
> 2. **What you'll see after that**: The dashboard's bar asks once (Yes / No thanks); Yes brings up Chrome's 'Allow notifications?', tap Allow; the bar never comes back. Without the setting, the bar gives these steps instead.
>    Action: In the card; f12-01 already builds it this way
> 3. **Done when, reworded**: First the ticket merged, then your one-time Chrome setting on both devices, then a test notification on both.
>    Action: F12 Done when edited
> 4. **Repeats**: None, F51 to F58 included.
>    Action: Nothing
>
> Proposals:
> - F12: notifications that really arrive, asked once (plan)

## The owner, 2026-10-08 23:25

> I sent back your proposal “F12: notifications that really arrive, asked once” (f12-plan).
> - On its key point 1 (How it works for you): Will there be instructions on how to do that somewhere

## The lead, 2026-10-08 23:27

> Yes: the dashboard will show you the steps itself until Chrome trusts its address, and I've added that to the card and to ticket f12-01.
>
> 1. **Where the instructions are**: In the dashboard itself. Until Chrome trusts the address, the bar under the top bar says it can't show notifications yet and lists the three steps. Your own address is already filled in, and each of the two things you need to paste has a Copy button. A web page can't link to Chrome's settings, so copying is the closest it can get. The same steps are also on the F12 card and in ADR 26 item 1.
>    Action: Ticket f12-01 changed: the bar shows the steps with Copy buttons, and its test checks the steps appear with the page's own address. The card says where the steps live.
> 2. **After you tap 'Got it'**: As agreed, the bar won't show again in that browser, so the steps stay on the card and in ADR 26. I recommend leaving it like this rather than keeping the bar until the setup is done: you set this up once per device, and a bar that won't go away is the kind of nagging you didn't want.
>    Action: Nothing
> 3. **No need to pause**: f12-01 is still waiting in tasks/later, so nothing can start on it while we talk.
>    Action: Nothing
>
> Proposals:
> - F12: notifications that really arrive, asked once (plan)
