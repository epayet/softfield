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

// f210-03: typed comments that wait in the browser tab across steps
(function () {
  const KEY = "softfield-comments";
  function _path() {
    return window.location.pathname + window.location.search;
  }
  function _load() {
    try {
      return JSON.parse(sessionStorage.getItem(KEY)) || {};
    } catch {
      return {};
    }
  }
  function _save(obj) {
    sessionStorage.setItem(KEY, JSON.stringify(obj));
  }
  window._saveComment = function () {
    const page = _load();
    page[_path()] = Array.from(document.querySelectorAll("textarea.comment"))
      .filter((t) => t.value.trim())
      .map((t) => [t.dataset.point, t.value]);
    _save(page);
  };
  window._restoreComments = function () {
    const page = _load();
    const path = _path();
    const stored = page[path];
    if (!stored || !stored.length) return;
    const latest = document.querySelector("[data-latest]")?.dataset.latest;
    const storedLatest = stored._latest;
    if (latest && storedLatest && storedLatest !== latest) return; // older message
    for (const [n, text] of stored) {
      const box = document.querySelector(
        `textarea.comment[data-point="${n}"]`
      );
      if (box) {
        box.value = text;
        // Open the box: details for thread, label for proposal
        const parent = box.parentElement;
        if (parent.tagName === "DETAILS" && !parent.open) {
          parent.open = true;
        } else if (parent.tagName === "LABEL") {
          parent.hidden = false;
          parent.style.display = "flex";
        }
      }
    }
    // Update the strip's unsent counts
    const unsendEl = document.getElementById("card-steps")?.dataset.unsend;
    if (!unsendEl) return;
    const unsend = JSON.parse(unsendEl);
    for (const [n, text] of stored) {
      unsend[n] = (unsend[n] || 0) + 1;
    }
    const nav = document.getElementById("card-steps");
    if (nav) nav.dataset.unsend = JSON.stringify(unsend);
  };
  window._clearPageComments = function () {
    const page = _load();
    delete page[_path()];
    _save(page);
  };
  // Restore on load
  window._restoreComments();
  // Save on input
  document.addEventListener("input", (e) => {
    if (e.target.classList.contains("comment")) window._saveComment();
  });
  // Restore after htmx swap
  document.addEventListener("htmx:afterSettle", () => {
    window._restoreComments();
  });
})();
