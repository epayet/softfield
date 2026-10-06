// Browser notifications while a dashboard page is open (f5-12, ADR 18 item 4). The top bar's
// "Notify me" asks permission, never on load. Once allowed, base.html's #notify-live polls
// /live for its #live-facts: the open Needs-you items (id -> text) and whether all the work is
// done. After each swap this compares them with what it saw last and notifies once per new
// item, and once when all done turns true. What it saw is kept per project in localStorage, so
// moving to another page or a second tab doesn't notify again. No service worker: nothing
// shows once every dashboard page is closed (push to a closed page is in the roadmap).
"use strict";

(() => {
  const supported = "Notification" in window;
  const FRESH = 60_000; // ms: an older look (the dashboard was closed) is a first look again

  window.notifyOn = () => supported && Notification.permission === "granted";

  function show(title, body, tag) {
    try {
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

  // The button: shown where the browser can notify; disabled, with the reason, where it can't.
  function offer(button) {
    if (!supported || Notification.permission === "granted") return;
    button.hidden = false;
    if (!window.isSecureContext) {
      button.disabled = true;
      button.title = "Browsers notify only over https or on this computer (127.0.0.1)";
    } else if (Notification.permission === "denied") {
      button.disabled = true;
      button.title = "Blocked: allow notifications in the browser's site settings";
    } else {
      button.addEventListener("click", async () => {
        await Notification.requestPermission();
        button.hidden = Notification.permission === "granted";
        if (Notification.permission === "denied") offer(button);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("notify-me");
    if (button) offer(button);
    document.body.addEventListener("htmx:afterSwap", (event) => {
      const facts = event.target.querySelector("#live-facts");
      if (facts && window.notifyOn()) compare(facts);
    });
  });
})();
