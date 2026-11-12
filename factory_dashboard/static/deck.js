// One point at a time on a phone (f6-10). Each .deck's children are its points; the .deck-nav
// right after it holds a dot per point and the ◀ ▶ buttons. dashboard.css hides the .off points
// and shows the nav only under 640 px, so on wider screens this changes nothing you see.
const deckUp = (deck) => {
  if (deck.dataset.up) return; // bound once per deck drawn
  deck.dataset.up = "1";
  const points = Array.from(deck.children);
  const nav = deck.nextElementSibling;
  if (!nav || !nav.classList.contains("deck-nav")) return; // no points, no nav
  const dots = Array.from(nav.querySelectorAll(".deck-dots span"));
  const [previous, next] = nav.querySelectorAll(".deck-arrows button");
  let at = 0;
  const show = () => {
    points.forEach((p, i) => p.classList.toggle("off", i !== at));
    dots.forEach((d, i) => {
      d.classList.toggle("at", i === at);
      const comments = Array.from(points[i].querySelectorAll("textarea.comment"));
      d.classList.toggle("commented", comments.some((t) => t.value.trim()));
    });
    previous.disabled = at === 0;
    next.disabled = at === points.length - 1;
  };
  previous.addEventListener("click", () => { at -= 1; show(); });
  next.addEventListener("click", () => { at += 1; show(); });
  // typing marks the dot; the review's Comment… button clears its box on a second tap
  deck.addEventListener("input", show);
  deck.addEventListener("click", show);
  show();
};
document.querySelectorAll(".deck").forEach(deckUp);
// the conversation drawn again (a send, or the lead's answer arriving: F19) brings its decks up
document.addEventListener("htmx:afterSettle", () => document.querySelectorAll(".deck").forEach(deckUp));

// f210-03, f210-05 (F210 D5): comments typed on a thread's or a proposal's points wait in this
// browser tab (sessionStorage, by page path) across the card's steps. They come back in their
// open boxes, the strip says which step holds some, and a successful send clears them. On a
// thread they wait for the lead's latest message only (#conversation-stamp's data-latest).
(() => {
  const KEY = "softfield-comments";
  const load = () => {
    try {
      return JSON.parse(sessionStorage.getItem(KEY)) || {};
    } catch {
      return {};
    }
  };
  const save = (all) => sessionStorage.setItem(KEY, JSON.stringify(all));
  const latest = () => document.getElementById("conversation-stamp")?.dataset.latest || "";
  const boxes = () => Array.from(document.querySelectorAll("textarea.comment"));
  const counted = (entry) => (entry && Array.isArray(entry.comments) ? entry.comments.length : 0);
  // each step's link says how many comments wait on its page, counted afresh every time
  const strip = () => {
    const all = load();
    document.querySelectorAll("#card-steps a").forEach((a) => {
      a.querySelector("small.not-sent")?.remove();
      const n = counted(all[new URL(a.href).pathname]);
      a.classList.toggle("unsent", n > 0);
      if (!n) return;
      const note = document.createElement("small");
      note.className = "not-sent";
      note.textContent = `${n} comment${n === 1 ? "" : "s"} not sent`;
      a.append(note);
    });
  };
  const keep = () => {
    const all = load();
    const comments = boxes().filter((t) => t.value.trim()).map((t) => [t.dataset.point, t.value]);
    if (comments.length) all[location.pathname] = { latest: latest(), comments };
    else delete all[location.pathname];
    save(all);
    strip();
  };
  const restore = () => {
    const all = load();
    const entry = all[location.pathname];
    const filled = [];
    if (entry && entry.latest !== latest()) {
      delete all[location.pathname]; // typed under an older message of the lead's
      save(all);
    } else if (entry) {
      for (const [n, text] of entry.comments) {
        const box = document.querySelector(`textarea.comment[data-point="${n}"]`);
        if (!box || box.value.trim()) continue;
        box.value = text;
        const details = box.closest("details");
        if (details) details.open = true;
        filled.push(box);
      }
    }
    // the page's own counters (the thread's progress, the deck's dots, the review's buttons)
    filled.forEach((box) => box.dispatchEvent(new Event("input", { bubbles: true })));
    if (filled.length) document.dispatchEvent(new Event("comments-restored"));
    strip();
  };
  // called by the page after a successful send; a failed one keeps them
  window.sentComments = () => {
    const all = load();
    delete all[location.pathname];
    save(all);
    boxes().forEach((box) => {
      box.value = "";
      box.dispatchEvent(new Event("input", { bubbles: true }));
    });
    strip();
  };
  document.addEventListener("input", (e) => {
    if (e.target.matches && e.target.matches("textarea.comment")) keep();
  });
  document.addEventListener("htmx:afterSettle", restore);
  restore();
})();
