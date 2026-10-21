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
