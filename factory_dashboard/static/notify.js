// Browser notifications while a dashboard page is open (f5-12, ADR 18 item 4).
// The dashboard asks once with its own bar (f12-01, ADR 26 item 2) and uses a
// service worker to show notifications on Android too (f12-01, ADR 26 item 3).
// base.html's #live-poll fetches /live's #live-facts every 5 s (f6-16): the open
// Needs-you items (id -> text) and whether all the work is done. Once allowed,
// after each swap this compares them with what it saw last and notifies once per
// new item, and once when all done turns true. What it saw is kept per project in
// localStorage, so moving to another page or a second tab doesn't notify again.
"use strict";

(() => {
  const supported = "Notification" in window;
  const FRESH = 60_000; // ms: an older look (the dashboard was closed) is a first look again

  window.notifyOn = () => supported && Notification.permission === "granted";

  // The service worker registration (f12-01, ADR 26 item 3).
  let registration = null;

  function show(title, body, tag) {
    try {
      if (registration) {
        registration.showNotification(title, { body, tag }).catch(() => {
          new Notification(title, { body, tag }).onclick = () => window.focus();
        });
        return;
      }
      const note = new Notification(title, { body, tag });
      note.onclick = () => window.focus();
    } catch (error) {
      // Chrome on Android shows only a service worker's notifications, and there is none
      console.warn("notify:", error);
    }
  }

  function compare(facts) {
    const key = "notify:" + facts.dataset.project;
    const needs = JSON.parse(facts.dataset.needs);
    const done = facts.dataset.allDone === "true";
    const before = JSON.parse(localStorage.getItem(key) || "null");
    localStorage.setItem(key, JSON.stringify({ ids: Object.keys(needs), done, at: Date.now() }));
    if (!before || Date.now() - before.at > FRESH) return; // what is already there isn't news
    for (const [id, text] of Object.entries(needs)) {
      if (!before.ids.includes(id)) show("Needs you", text, id);
    }
    if (done && !before.done) show("All work done", "The queue is empty and nothing runs.", "all-done");
  }

  // The notification permission bar (f12-01, ADR 26 item 2).
  function setupBar() {
    if (!supported) return;
    const bar = document.getElementById("notify-bar");
    if (!bar) return;

    if (window.isSecureContext) {
      if (Notification.permission !== "default") return;
      if (localStorage.getItem("notify:asked")) return;
      bar.querySelector("[role=body]").textContent =
        "Get a notification when something needs you, or when all the work is done?";
      bar.querySelector('[data-action="yes"]').addEventListener("click", async () => {
        bar.hidden = true;
        // Chrome's prompt closed without an answer leaves "default": ask again on the next page
        if ((await Notification.requestPermission()) !== "default") {
          localStorage.setItem("notify:asked", "1");
        }
      });
      bar.querySelector('[data-action="no"]').addEventListener("click", () => {
        localStorage.setItem("notify:asked", "1");
        bar.hidden = true;
      });
    } else {
      // Chrome answers "denied" on an address it doesn't trust, so the steps don't wait for
      // "default". "Got it" has its own key: the question still comes once the address is
      // trusted (f12 review, F1 and F2).
      if (localStorage.getItem("notify:steps")) return;
      const origin = location.origin;
      bar.querySelector("[role=body]").innerHTML =
        "This address can&#39;t show notifications yet. In Chrome: " +
        "1. open <code>chrome://flags/#unsafely-treat-insecure-origin-as-secure</code> " +
        '<button type="button" class="copy-link" data-copy="' +
        encodeURIComponent("chrome://flags/#unsafely-treat-insecure-origin-as-secure") +
        '">Copy</button> ' +
        "in a new tab; " +
        "2. paste this address in its box: <code class=\"origin-code\">" +
        origin +
        "</code> " +
        '<button type="button" class="copy-link" data-copy="' +
        encodeURIComponent(origin) +
        '">Copy</button>; ' +
        "3. set it to Enabled and tap Relaunch. Then come back here.";
      for (const btn of bar.querySelectorAll(".copy-link")) {
        btn.addEventListener("click", async () => {
          const text = decodeURIComponent(btn.dataset.copy);
          try {
            await navigator.clipboard.writeText(text);
          } catch (_) {
            const ta = document.createElement("textarea");
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
          }
          btn.textContent = "Copied";
        });
      }
      bar.querySelector('[data-action="got-it"]').addEventListener("click", () => {
        localStorage.setItem("notify:steps", "1");
        bar.hidden = true;
      });
      bar.querySelector('[data-action="yes"]').hidden = true;
      bar.querySelector('[data-action="no"]').hidden = true;
      bar.querySelector('[data-action="got-it"]').removeAttribute("hidden");
    }
    bar.hidden = false;
  }

  // Register the service worker (f12-01, ADR 26 item 3).
  async function registerSw() {
    if (!navigator.serviceWorker) return;
    try {
      registration = await navigator.serviceWorker.register("/static/sw.js");
    } catch (_) {
      // Ignore: the SW may not be available.
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupBar();
    registerSw();
    document.body.addEventListener("htmx:afterSwap", (event) => {
      const facts = event.target.querySelector("#live-facts");
      if (facts && window.notifyOn()) compare(facts);
    });
  });
})();
