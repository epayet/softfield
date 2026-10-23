// The board's field (F15 D2): under 900 px one stage shows at a time, the planted one at first
// or the one the address names (#stage-ripe), and a press on a plot shows its stage. From
// 900 px dashboard.css shows every stage whatever is picked, so a plot is only a count there.
// Without this script every stage shows, stacked.
//
// The board's order (F15 D1, D3, D9, after .factory/cards/f15-mockup/board-edit.html): a card
// of a stage the owner orders is dragged by its grip, or moved with its ⋯ menu, inside its
// stage. What is out of place is worked out from the order, not from what was touched, and
// shows dashed until sent. "Send new order" posts one reorder: the page's whole open line
// (#board-line), each moved card just before the card it was dropped above. Then the field is
// fetched again and shows the order on its way.
(() => {
  const field = document.getElementById("field");
  const plots = [...document.querySelectorAll(".plot")];
  if (!field || !plots.length) return;
  const stages = plots.map((plot) => plot.dataset.stage);
  const named = () => {
    const stage = location.hash.replace(/^#stage-/, "");
    return stages.includes(stage) ? stage : null;
  };
  const show = (stage) => {
    field.dataset.shown = stage;
    for (const plot of plots) plot.setAttribute("aria-pressed", String(plot.dataset.stage === stage));
    for (const column of field.querySelectorAll(".stage")) {
      column.classList.toggle("shown", column.id === `stage-${stage}`);
    }
  };
  for (const plot of plots) {
    plot.addEventListener("click", () => {
      show(plot.dataset.stage);
      // the address keeps the stage for a reload, without the jump a link would make
      history.replaceState(null, "", `#stage-${plot.dataset.stage}`);
    });
  }
  addEventListener("hashchange", () => named() && show(named()));
  show(named() || "planted");

  const PLACED = ["seed", "sprouting", "planted"]; // the stages the owner orders
  const bar = document.getElementById("order-bar");
  const sheet = document.getElementById("order-sheet");
  let stageOf = {}; // each open card's stage, by its key
  let came = []; // the open line as the page came
  let line = []; // and as moved now
  let moved = new Set();

  const inStage = (keys, stage) => keys.filter((key) => stageOf[key] === stage);
  const slot = (key) => field.querySelector(`.slot[data-key="${CSS.escape(key)}"]`);
  const shownIn = (stage) => [...field.querySelectorAll(`.slot[data-stage="${stage}"]`)].map((s) => s.dataset.key);

  // The cards out of place between two orders: those outside their longest common run, as
  // board.py's _out_of_place. A card put back where it was is not moved, nor the cards it passed.
  const outOfPlace = (before, after) => {
    const n = before.length, m = after.length;
    const run = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
    for (let i = n - 1; i >= 0; i--) {
      for (let j = m - 1; j >= 0; j--) {
        run[i][j] = before[i] === after[j] ? run[i + 1][j + 1] + 1 : Math.max(run[i + 1][j], run[i][j + 1]);
      }
    }
    const kept = new Set();
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (before[i] === after[j]) { kept.add(before[i]); i++; j++; }
      else if (run[i][j + 1] >= run[i + 1][j]) j++;
      else i++;
    }
    return after.filter((key) => !kept.has(key));
  };

  // Each card in its place, marked when moved, and the bar while anything is
  const work = () => {
    moved = new Set();
    for (const stage of PLACED) {
      const now = inStage(line, stage), before = inStage(came, stage);
      for (const key of outOfPlace(before, now)) moved.add(key);
      const list = field.querySelector(`#stage-${stage} .cards`);
      const slots = now.map(slot).filter(Boolean);
      for (const s of slots) list.append(s);
      for (const s of slots) {
        const key = s.dataset.key, card = s.querySelector(".card"), out = moved.has(key);
        const place = card.querySelector(".card-meta b");
        if (place) place.textContent = `#${now.indexOf(key) + 1}`;
        card.classList.toggle("moved", out);
        const way = card.querySelector(".card-way:not(.card-moved)");
        if (way) way.hidden = out; // the order on its way, replaced by this one
        let note = card.querySelector(".card-moved");
        if (out && !note) {
          note = document.createElement("span");
          note.className = "card-way card-moved";
          card.append(note);
        }
        if (out) note.textContent = `moved · was #${before.indexOf(key) + 1} · not sent yet`;
        else if (note) note.remove();
      }
    }
    bar.hidden = !moved.size;
    document.body.classList.toggle("has-order-bar", !bar.hidden);
    bar.querySelector("p").textContent =
      `${moved.size} card${moved.size === 1 ? "" : "s"} moved. Nothing is sent yet.`;
  };

  // ``key`` goes just before ``before`` in the whole line, or just after ``after``
  const move = (key, { before = null, after = null }) => {
    if (key === before || key === after) return;
    const rest = line.filter((k) => k !== key);
    rest.splice(before !== null ? rest.indexOf(before) : rest.indexOf(after) + 1, 0, key);
    line = rest;
    work();
  };

  // The menu: Top, Up, Down and Bottom among the cards shown in the card's stage
  let menuFor = null;
  const moves = {
    top: (shown, i) => i > 0 && { before: shown[0] },
    up: (shown, i) => i > 0 && { before: shown[i - 1] },
    down: (shown, i) => i < shown.length - 1 && { after: shown[i + 1] },
    bottom: (shown, i) => i < shown.length - 1 && { after: shown[shown.length - 1] },
  };
  for (const button of sheet.querySelectorAll("[data-move]")) {
    button.addEventListener("click", () => {
      const { key, stage, opener } = menuFor;
      const shown = shownIn(stage);
      const to = moves[button.dataset.move](shown, shown.indexOf(key));
      if (to) move(key, to);
      sheet.close();
      opener.focus();
    });
  }

  // Drag: the card follows the pointer, a line shows where it lands, the page scrolls near its
  // top and bottom edges. It lands among its own stage's cards only.
  let drag = null;
  const target = () => {
    const others = [...drag.node.parentNode.querySelectorAll(".slot")].filter((n) => n !== drag.node);
    const above = others.find((n) => { const r = n.getBoundingClientRect(); return drag.y < r.top + r.height / 2; });
    return { others, above };
  };
  const tick = () => {
    if (!drag) return;
    const edge = 90, h = innerHeight, foot = bar.hidden ? 0 : bar.offsetHeight;
    if (drag.y < edge) scrollBy(0, -Math.ceil((edge - drag.y) / 6));
    else if (drag.y > h - edge - foot) scrollBy(0, Math.ceil((drag.y - (h - edge - foot)) / 6));
    drag.node.style.transform = `translateY(${drag.y - drag.y0 + scrollY - drag.s0}px)`;
    const { others, above } = target();
    for (const n of others) n.classList.remove("drop-before", "drop-after");
    if (above) above.classList.add("drop-before");
    else if (others.length) others[others.length - 1].classList.add("drop-after");
    drag.frame = requestAnimationFrame(tick);
  };
  const onMove = (e) => { if (drag) { drag.y = e.clientY; e.preventDefault(); } };
  const endDrag = () => {
    if (!drag) return;
    cancelAnimationFrame(drag.frame);
    const { others, above } = target();
    const node = drag.node;
    drag = null;
    removeEventListener("pointermove", onMove);
    removeEventListener("pointerup", endDrag);
    removeEventListener("pointercancel", endDrag);
    node.classList.remove("dragging");
    node.style.transform = "";
    for (const n of others) n.classList.remove("drop-before", "drop-after");
    if (above) move(node.dataset.key, { before: above.dataset.key });
    else if (others.length) move(node.dataset.key, { after: others[others.length - 1].dataset.key });
  };
  const startDrag = (e, node) => {
    if (drag || e.button !== 0) return;
    e.preventDefault();
    drag = { node, y0: e.clientY, s0: scrollY, y: e.clientY };
    node.classList.add("dragging");
    addEventListener("pointermove", onMove, { passive: false });
    addEventListener("pointerup", endDrag);
    addEventListener("pointercancel", endDrag);
    drag.frame = requestAnimationFrame(tick);
  };

  // Each card of a stage the owner orders gets its grip and its ⋯
  const button = (cls, text, label) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = cls;
    b.textContent = text;
    b.setAttribute("aria-label", label);
    return b;
  };
  const setUp = () => {
    const sent = JSON.parse(document.getElementById("board-line").textContent);
    stageOf = Object.fromEntries(sent);
    came = sent.map(([key]) => key);
    line = came.slice();
    for (const s of field.querySelectorAll(".slot")) {
      if (!PLACED.includes(s.dataset.stage)) continue;
      const card = s.querySelector(".card");
      const name = card.querySelector(".card-meta span").textContent;
      const grip = button("grip", "⠿", `Drag ${name}`);
      grip.addEventListener("pointerdown", (e) => startDrag(e, s));
      const more = button("more", "⋯", `Move ${name}`);
      more.addEventListener("click", () => {
        menuFor = { key: s.dataset.key, stage: s.dataset.stage, opener: more };
        sheet.querySelector("h3").textContent = `${name} · ${card.querySelector(".card-title").textContent}`;
        sheet.showModal();
      });
      s.classList.add("movable");
      s.prepend(grip);
      s.append(more);
    }
    work();
  };

  bar.querySelector('[data-order="cancel"]').addEventListener("click", () => {
    line = came.slice();
    work();
  });
  const send = bar.querySelector('[data-order="send"]');
  const say = bar.querySelector("p");
  send.addEventListener("click", async () => {
    send.disabled = true;
    say.textContent = "Sending…";
    const body = new URLSearchParams({ kind: "reorder", project: field.dataset.project, value: JSON.stringify(line) });
    try {
      const asked = await fetch("/requests", { method: "POST", headers: { "HX-Request": "true" }, body });
      if (!asked.ok) throw new Error(String(asked.status));
    } catch {
      send.disabled = false;
      say.textContent = "Not sent: the dashboard didn't take it. Your moves are kept; try again.";
      return;
    }
    send.disabled = false;
    try {
      const page = new DOMParser().parseFromString(await (await fetch(location.href)).text(), "text/html");
      field.querySelector(".stages").replaceWith(page.querySelector("#field .stages"));
      document.getElementById("board-line").textContent = page.getElementById("board-line").textContent;
    } catch {
      location.reload(); // sent: the page as it is now shows it on its way
      return;
    }
    show(field.dataset.shown);
    setUp();
  });
  setUp();
})();
