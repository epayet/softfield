// The board's field (F15 D2): under 900 px one stage shows at a time, the planted one at first
// or the one the address names (#stage-ripe), and a press on a plot shows its stage. From
// 900 px dashboard.css shows every stage whatever is picked, so a plot is only a count there.
// Without this script every stage shows, stacked.
//
// The board's order (F15 D1, D3, D9, after .softfield/cards/f15-mockup/board-edit.html): a card
// of a stage the owner orders is dragged by its grip, or moved with its ⋯ menu, inside its
// stage. What is out of place is worked out from the order, not from what was touched, and
// shows dashed until sent. "Send new order" posts one reorder: the page's whole open line
// (#board-line), each moved card just before the card it was dropped above. Then the field is
// fetched again and shows the order on its way.
//
// The field follows the work (F209 D4–D6): every 10 s, and at once on coming back to the page,
// it fetches itself and swaps only the parts whose text changed since the last answer, so an
// unchanged board touches nothing. A drag, moves not sent, the ⋯ menu or liveIdle hold it, and
// the plate's small line says when it isn't fresh.
(() => {
  const field = document.getElementById("field");
  const plots = [...document.querySelectorAll(".plot")];
  if (!field || !plots.length) return;
  // The parts as the server last sent them: setUp and show change the page's own copy.
  const textOf = (doc) => ({
    now: doc.getElementById("board-now")?.outerHTML,
    stages: doc.querySelector("#field .stages")?.outerHTML,
    line: doc.getElementById("board-line")?.textContent,
  });
  let last = textOf(document);
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

  // The plate's small line (D6): moves not sent hold the refresh; a failed fetch says since when
  const EVERY = "refreshes every 10 s";
  let goodAt = new Date(); // the last good answer, the page's own load at first
  let failed = false;
  const clock = (d) => `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  const sayFresh = () => {
    const text = moved.size ? "Refresh held: your moves aren't sent yet"
      : failed ? `Not updated since ${clock(goodAt)}: the dashboard doesn't answer` : EVERY;
    for (const s of document.querySelectorAll("#board-now .fresh")) {
      s.textContent = text;
      s.classList.toggle("stale", text !== EVERY);
    }
  };

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
    sayFresh();
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

  // The card's own actions, copied from its slot's template on each ⋯ (F15 D7). "Set aside"
  // posts an archive request for its conversation, which the runner does at its next pick.
  const actions = sheet.querySelector(".order-actions");
  actions.addEventListener("click", async (e) => {
    const aside = e.target.closest(".set-aside");
    if (!aside || aside.disabled) return;
    const { key } = menuFor;
    aside.disabled = true;
    aside.textContent = "Set aside · on its way";
    const body = new URLSearchParams({
      kind: "archive", project: field.dataset.project, subject: aside.dataset.thread, value: "on",
    });
    try {
      const asked = await fetch("/requests", { method: "POST", headers: { "HX-Request": "true" }, body });
      if (!asked.ok) throw new Error(String(asked.status));
    } catch {
      aside.disabled = false;
      aside.textContent = "Set aside · not sent, try again";
      return;
    }
    // the slot's own copy says so too, for the next ⋯ before the page is fetched again
    const own = slot(key)?.querySelector("template.card-actions")?.content.querySelector(".set-aside");
    if (own) { own.disabled = true; own.textContent = aside.textContent; }
  });

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
      const more = button("more", "⋯", `Actions for ${name}`);
      more.addEventListener("click", () => {
        menuFor = { key: s.dataset.key, stage: s.dataset.stage, opener: more };
        sheet.querySelector("h3").textContent = `${name} · ${card.querySelector(".card-title").textContent}`;
        const own = s.querySelector("template.card-actions");
        actions.replaceChildren(...(own ? [own.content.cloneNode(true)] : []));
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

  // What holds the 10 s fetch, and drops an answer that comes back into it (D5)
  const busy = () => Boolean(drag || moved.size || sheet.open);

  // Redraw the field as it is now, past the browser's cache: after a send, on the way back, and
  // every 10 s (``follow``). False, with the page left as it is, when no board came; null when
  // a followed answer came into a drag, moves or the menu, and was dropped. A send redraws the
  // field whatever came; the 10 s fetch swaps only the parts whose text changed.
  const refresh = async (follow = false) => {
    let page;
    try {
      const answer = await fetch(location.href, { cache: "no-cache" });
      if (!answer.ok) return false;
      page = new DOMParser().parseFromString(await answer.text(), "text/html");
    } catch {
      return false;
    }
    const fresh = textOf(page);
    if (fresh.stages === undefined || fresh.line === undefined) return false;
    if (follow && busy()) return null;
    if (!follow || fresh.stages !== last.stages || fresh.line !== last.line) {
      field.querySelector(".stages").replaceWith(page.querySelector("#field .stages"));
      document.getElementById("board-line").textContent = fresh.line;
      show(field.dataset.shown);
      setUp(); // the grips and ⋯ of the new cards, only after a swap of .stages
    }
    const now = page.getElementById("board-now");
    if (now && fresh.now !== last.now) document.getElementById("board-now").replaceWith(now);
    // each plot keeps its node and its listener; only its count and its ripe light change
    for (const plot of plots) {
      const came = page.querySelector(`.plot[data-stage="${plot.dataset.stage}"]`);
      if (!came) continue;
      const count = came.querySelector("b").textContent;
      if (plot.querySelector("b").textContent !== count) plot.querySelector("b").textContent = count;
      plot.classList.toggle("ripe", came.classList.contains("ripe"));
    }
    last = fresh;
    sayFresh(); // a new plate comes with the template's words
    return true;
  };

  // Every 10 s, and at once on coming back to the page, unless something holds it (D5)
  let fetching = false;
  const follow = async () => {
    if (fetching || document.hidden || busy() || !window.liveIdle()) return;
    fetching = true;
    try {
      const drawn = await refresh(true);
      if (drawn === false) failed = true;
      else if (drawn) { failed = false; goodAt = new Date(); }
    } finally {
      fetching = false;
      sayFresh();
    }
  };
  setInterval(follow, 10000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) follow(); });

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
    if (!(await refresh())) location.reload(); // sent: the page as it is now shows it on its way
  });

  // Coming back with the phone's back button shows the field as it is now (D3): from the
  // browser's memory (persisted), or by back or forward, which may load the browser's old copy.
  addEventListener("pageshow", (event) => {
    const back = performance.getEntriesByType("navigation")[0]?.type === "back_forward";
    if (!event.persisted && !back) return; // normal load: fetch nothing
    if (moved.size) return; // moves not sent: keep them
    refresh();
  });

  setUp();
})();
