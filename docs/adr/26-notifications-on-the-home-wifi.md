# ADR 26: Notifications that work on the home Wi-Fi

- **Status:** Accepted (by the owner, 2026-10-08)
- **Date:** 2026-10-07
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 18](18-dashboard-writes.md) item 4 (notifications while a page is open) and item 1 (the dashboard on the home Wi-Fi, over plain http).
- **Evidence:** F12, the owner's thread (2026-10-07): "when i click on it, nothing happens right now even on desktop". The dashboard is reached at `http://<LAN address>:<port>` (`runner dashboard --lan`). Browsers allow notifications only on a secure address (https, or 127.0.0.1 on the same machine), so `factory_dashboard/static/notify.js` greys the button out there, and gives the reason only as a hover tooltip, which a phone never shows. On Android, Chrome also needs a service worker to show any notification, and the dashboard has none.

## Context
- f5-12 shipped notifications that were checked on 127.0.0.1 only; on the address the owner actually uses they could never work, on any device.
- Other sites ask once with their own small question ("Get notified? Yes / Not now") and call the browser's prompt only after a Yes. Firefox and Safari ignore a permission prompt that no tap started, and Chrome quietly hides prompts from sites that ask on load, so "ask on the first visit" has to be the site's own question first.
- Even once allowed, a phone freezes a background page after a few minutes, so a phone notifies only while the dashboard is open or was just left. Notifications with the page closed need something else (Consequences).

## Decisions (draft; ⚑ = deviates from an earlier decision)
1. **⚑ Each browser trusts the dashboard's address as secure.** Without a secure address no browser notifies, on any device. The dashboard keeps `runner dashboard --lan` and plain http at the machine's LAN IP; on the desktop and on the phone, Chrome is told once to treat that one address as secure: `chrome://flags/#unsafely-treat-insecure-origin-as-secure` → add `http://<LAN address>:<port>` → Relaunch. No code. A fixed address for this machine in the router keeps the setting valid.
2. **⚑ Asked once, on the first visit, not by a button.** A small bar under the top bar: "Get a notification when something needs you, or when all the work is done? [Yes] [No thanks]". Yes calls the browser's prompt. Either answer hides the bar for good in that browser; to change your mind later, use the browser's site settings. The top bar's "Turn on notifications" button goes (and with it the phone layout that put it on the left). On an address that can't notify, the bar says so in words, once, with "Got it".
3. **A small service worker shows the notifications** (`factory_dashboard/static/sw.js`): it only shows them and, on a tap, opens the dashboard. No push, no caching, no third party. This is what Android needs, and what web push would build on later.
4. **Unchanged:** what notifies (a new Needs-you item, all work done), the 5-second poll, one notification per item across pages and tabs, the dashboard on the home Wi-Fi only (no tunnel, no public host), and web push to a closed page staying in the roadmap.

## Settled with the owner
1. **A secure address by trusting it in each browser** (owner, 2026-10-08: option A). Costs accepted: it is per browser; it must be redone if the machine's LAN address changes; Chrome may drop the setting one day, and then B is the fallback.

The options weighed:
   - **A. Trust the address in each browser** (chosen): item 1. Two minutes per device, no code, nothing new to keep secret.
   - **B. https with your own certificate** (`mkcert`, which can issue a certificate for an IP address): the dashboard serves `https://<LAN address>:<port>`, and you install mkcert's root certificate once on each device (on Android: Settings → Security → Install a certificate). Works in every browser and is the basis browser web push needs. Costs: a code change and a new tool, and a root key on this machine that, if stolen, could fake any website on the devices that trust it.
   - **C. Tailscale `serve`** (tailnet only, not Funnel): a real certificate with nothing to install but the Tailscale app, already used for Coucou itself. ⚑ You chose the home Wi-Fi only, without Tailscale (2026-10-02), and the phone would need Tailscale on to see the dashboard.
   - **Not offered:** a self-signed certificate clicked through ("Proceed anyway"): browsers keep such a page from service workers, so it wouldn't fix the phone. Listening on 127.0.0.1 as well as the LAN address: helps only a browser on the factory machine itself, and widens what the dashboard listens on.

## Consequences
- F12 is one developer ticket (f12-01); the setup steps are item 1 here, and the dashboard's bar names them on an address not yet trusted. Nothing changes in how the dashboard is served.
- On the phone, notifications still come only while the dashboard is open or just left. If that isn't enough, the next step needs no secure address at all: the ntfy app on the phone, and a small ntfy server on this machine reached at its LAN IP over plain http. The runner posts to it when something needs you, and the phone shows it even with the dashboard closed and the screen off. It is a new always-on service and an app to install, so it is a later card, not F12. Browser web push would do the same but wants B or C.
