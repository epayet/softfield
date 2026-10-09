# Milestone F12: Turn on notifications  little feedback button

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Notes
The button on mobile is on the left rather than right. Also, what is it supposed to do? Do we even need it and just send notifications by default?

## Expected outcome
On the desktop and on the phone, the dashboard asks once, on the first visit, whether to notify you, and after a Yes it really does: a notification when something new needs you, and when all the work is done, while a dashboard page is open.

## How it works for you
Chrome never asks to trust the address: you change one of its settings by hand, once per device. Then the dashboard asks, once.
1. **Once, in Chrome, on each device** (the desktop, the phone). Type `chrome://flags/#unsafely-treat-insecure-origin-as-secure` in the address bar. On that page, write the dashboard's address in the box (the one you open today, e.g. `http://192.168.1.20:8765`), switch the setting to Enabled, and tap Relaunch. Chrome now treats that one address as secure.
2. **On your next visit to the dashboard,** a bar under the top bar asks: "Get a notification when something needs you, or when all the work is done? Yes / No thanks".
3. **Tap Yes:** Chrome's own small prompt appears ("Allow notifications?"). Tap Allow. The bar never comes back in that browser.
4. **From then on,** while a dashboard page is open (or was just left, on the phone), a notification pops up when something new needs you, and when all the work is done.

**Where you'll find these steps:** the dashboard itself shows them. Until Chrome trusts the address, the bar says the address can't show notifications yet and gives step 1, numbered, with your own address already filled in and a Copy button for each of the two things to paste (a web page can't open Chrome's settings with a link). "Got it" hides the bar for good; the steps stay here and in [ADR 26](../adr/26-notifications-on-the-home-wifi.md) item 1.

## Done when
- f12-01 merged: the first-visit bar replaces the top bar's button, and a service worker shows the notifications
- you've done step 1 on your desktop and your phone ([ADR 26](../adr/26-notifications-on-the-home-wifi.md) item 1: your one-time setting, no code)
- you get a test notification on both devices (the review's hand check)

## Why it failed
f5-12 was checked on 127.0.0.1 only. The owner opens the dashboard at its LAN address over http, where browsers refuse notifications: the button was greyed out, with the reason in a hover tooltip a phone can't show. On Android, Chrome also needs a service worker, and there was none.

## Tickets
- `f12-01-notifications-asked-once` (developer): the bar, the service worker, the button removed.

## Not in this milestone
Notifications with every dashboard page closed: the roadmap. The simplest way there is the ntfy app on the phone with a small ntfy server on this machine, over plain http at its LAN IP ([ADR 26](../adr/26-notifications-on-the-home-wifi.md), Consequences); browser web push would want option B or C.
