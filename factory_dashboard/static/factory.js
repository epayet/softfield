// The factory line (f3 D11): draws svg#floor from the document in the JSON block
// #factory-line that line.py's live_line wrote. Every rule lives in that document; this only
// lays it out, as hand-written SVG after docs/milestones/f3-line-mockup/Line.dc.html, coloured
// by the stylesheet's tokens. htmx swaps the floor in every 5 s, and it is drawn again.
"use strict";

(() => {
  const NS = "http://www.w3.org/2000/svg";

  function add(parent, tag, attrs = {}, words = null) {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value !== null && value !== undefined) node.setAttribute(key, value);
    }
    if (words !== null) node.textContent = words;
    parent.appendChild(node);
    return node;
  }

  const text = (parent, x, y, words, cls = "", attrs = {}) =>
    add(parent, "text", { x, y, class: cls, ...attrs }, words);
  const short = (ticket) => ticket.split("-").slice(0, 2).join("-");
  const cut = (words, n) => (words && words.length > n ? `${words.slice(0, n - 1)}…` : words || "");
  const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

  // --- the belts: where each D11 belt runs, and where its words go -------------------------

  let _prev = {};

  const BELTS = {
    "seeds→planting": { path: "M150 140 L176 140", at: [163, 128], middle: true, short: true },
    "planting→rows": { path: "M238 196 L238 262", at: [250, 236] },
    "rows→queue": { path: "M294 500 L360 500", at: [300, 488] },
    "queue→lead": { path: "M470 360 L520 360 L520 210 L560 210", at: [534, 320], turn: true },
    "queue→developers": { path: "M462 480 L560 480", at: [470, 468] },
    "lead→checks": { path: "M790 205 L1010 205 L1010 260", at: [800, 194] },
    "developers→checks": { path: "M978 440 L1000 440 L1000 380", at: [1026, 410] },
    "checks→developers": { path: "M1019 380 L1019 600 L626 600 L626 512", at: [700, 592], back: true, thin: true },
    "checks→lead": { path: "M1040 260 L1040 236 L790 236", at: [800, 254], back: true, thin: true },
    "checks→merged": { path: "M1056 320 L1120 320", at: [1062, 308] },
    "merged→ripe": { path: "M1213 270 L1213 214", at: [1222, 246] },
    "ripe→stash": { path: "M1306 150 L1316 150 L1316 470 L1306 470", at: [1300, 320], turn: true, end: true },
    "merged→reviewers": { path: "M1150 270 L1150 248 L1080 248 L1080 162", at: [1145, 264], end: true },
  };

  function belt(svg, b) {
    const where = BELTS[b.id];
    if (!where) return;
    const cls = ["belt", where.back ? "back" : "", b.carrying ? "carrying" : "", b.carrying ? "moving" : ""].join(" ").trim();
    const g = add(svg, "g", { class: cls, "data-belt": b.id });
    add(g, "title", {}, b.label);
    const width = where.thin ? 10 : 13;
    add(g, "path", { d: where.path, class: "bed", "stroke-width": width + 5 });
    add(g, "path", { d: where.path, class: "rollers", "stroke-width": width });
    const words = b.today === null ? (where.short ? "" : b.label) : where.short ? `${b.today}` : `${b.label} · ${b.today}`;
    const [x, y] = where.at;
    const attrs = {};
    if (where.turn) attrs.transform = `rotate(-90 ${x} ${y})`;
    if (where.middle) attrs["text-anchor"] = "middle";
    if (where.end) attrs["text-anchor"] = "end";
    text(g, x, y, words, "", attrs);
  }

  // --- the field ----------------------------------------------------------------------------

  function station(svg, id) {
    return add(svg, "g", { class: "station", "data-station": id });
  }

  function field(svg, doc, count) {
    add(svg, "rect", { x: 12, y: 34, width: 300, height: 590, class: "field-plot" });
    text(svg, 26, 56, "THE FIELD", "head");

    const seeds = station(svg, "seeds");
    add(seeds, "path", { d: "M40 90 L150 90 L132 196 L58 196 Z", class: "unit" });
    const spots = [[80, 170], [98, 178], [114, 168], [90, 156], [108, 150], [72, 156], [122, 154], [100, 140]];
    spots.slice(0, Math.min(doc.field.seeds, spots.length)).forEach(([cx, cy]) =>
      add(seeds, "ellipse", { cx, cy, rx: 7, ry: 5, class: "seed" }));
    text(seeds, 95, 216, "SEEDS", "head", { "text-anchor": "middle" });
    text(seeds, 95, 232, `${plural(count.seeds, "ticket", "tickets")} set aside`, "dim", { "text-anchor": "middle" });

    const planting = station(svg, "planting");
    add(planting, "rect", { x: 176, y: 92, width: 124, height: 104, class: "unit" });
    add(planting, "rect", { x: 262, y: 58, width: 22, height: 34, class: "unit" });
    text(planting, 238, 120, "PLANTING", "head", { "text-anchor": "middle" });
    text(planting, 238, 138, "the lead plans", "", { "text-anchor": "middle" });
    text(planting, 238, 152, "with you", "", { "text-anchor": "middle" });
    text(planting, 238, 178, `${count.planting} sprouting`, "dim", { "text-anchor": "middle" });

    const rows = station(svg, "rows");
    add(rows, "rect", { x: 30, y: 262, width: 264, height: 300, class: "soil" });
    text(rows, 40, 284, "PLANTED ROWS", "head");
    doc.field.rows.slice(0, 4).forEach((row, n) => {
      const y = 316 + n * 58;
      const g = add(rows, "g", { "data-row": row.key });
      add(g, "path", { class: "sprout", d: `M50 ${y + 14} v-22 M50 ${y + 2} c-8 0-11-4-11-9 8 0 11 4 11 9 M50 ${y - 2} c0-7 3-10 10-10 0 7-3 10-10 10` });
      text(g, 70, y - 2, cut(`${row.key.toUpperCase()} · ${row.title || ""}`, 30), "name");
      add(g, "rect", { x: 70, y: y + 6, width: 200, height: 7, class: "bar-bg" });
      add(g, "rect", { x: 70, y: y + 6, width: row.total ? (200 * row.done) / row.total : 0, height: 7, class: "bar-fill" });
      const running = row.running ? ` · ${row.running} running` : "";
      text(g, 70, y + 28, `${row.done} of ${row.total} merged · ${row.ready} ready${running}`, "dim");
    });
    if (doc.field.rows.length > 4) text(rows, 40, 540, `+ ${doc.field.rows.length - 4} more`, "dim");
    const queued = doc.field.rows.reduce((sum, row) => sum + row.ready, 0);
    text(rows, 40, 552, `${plural(count.rows, "row feeds", "rows feed")} ${plural(queued, "ticket", "tickets")} →`, "dim");
  }

  // --- the queue ----------------------------------------------------------------------------

  function queue(svg, doc) {
    const g = station(svg, "queue");
    add(g, "path", { d: "M360 330 L470 330 L452 560 L378 560 Z", class: "unit" });
    text(g, 415, 320, `QUEUE · ${doc.queue.length}`, "head", { "text-anchor": "middle" });
    doc.queue.slice(0, 16).forEach((crate, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 380 + col * 38, y = 520 - row * 22;
      const c = add(g, "g", { "data-queue-crate": crate.ticket });
      add(c, "title", {}, `${crate.number} ${crate.ticket}: ${crate.title || ""}${crate.waits.length ? ` (after ${crate.waits.join(", ")})` : ""}`);
      add(c, "rect", { x, y, width: 34, height: 20, class: `crate ${crate.kind}${crate.waits.length ? " waits" : ""}` });
      text(c, x + 17, y + 14, String(crate.number), "on", { "text-anchor": "middle" });
    });
    if (doc.queue.length > 16) text(g, 415, 352, `+ ${doc.queue.length - 16} more`, "dim", { "text-anchor": "middle" });
    text(g, 415, 580, "in run order", "dim", { "text-anchor": "middle" });
  }

  // --- the machines -------------------------------------------------------------------------

  const AREAS = {  // where each machine station's machines go, side by side
    lead: { x: 560, y: 120, width: 230, height: 170, gap: 10 },
    reviewers: { x: 810, y: 50, width: 280, height: 112, gap: 10, most: 140 },
    developers: { x: 562, y: 404, width: 402, height: 108, gap: 12, most: 128 },
  };

  function machine(svg, m, x, y, w, h) {
    const cls = ["machine", m.station, m.state, m.stand_in ? "stand-in" : "", m.state === "working" ? "on" : ""].join(" ").trim();
    const g = add(svg, "g", { class: cls, "data-machine": m.id });
    add(g, "title", {}, `${m.name} · ${m.where} · ${m.state}${m.rating !== null ? ` · rated ${m.rating}` : ""}`);
    const tall = Math.round(30 * m.scale);
    if (m.station !== "reviewers") {
      add(g, "rect", { x: x + w - 34, y: y - tall, width: 18, height: tall, class: "unit" });
      if (m.state === "working") {
        add(g, "circle", { cx: x + w - 25, cy: y - tall - 10, r: 6, class: "smoke" });
        add(g, "circle", { cx: x + w - 18, cy: y - tall - 22, r: 8, class: "smoke" });
      }
    }
    add(g, "rect", { x, y, width: w, height: h, class: "unit" });
    const left = x + 10;
    let line = y + 20;
    const rated = m.rating !== null ? ` · rated ${m.rating}` : "";
    if (m.station === "lead") {
      text(g, left + 5, y + 25, "THE LEAD", "head big");
      add(g, "rect", { x: left + 5, y: y + 38, width: w - 30, height: 28, class: "plate" });
      text(g, left + 5 + (w - 30) / 2, y + 57, `${m.name.toUpperCase()}${rated}`, "on", { "text-anchor": "middle" });
      line = y + 88;
    } else {
      text(g, left, line, cut(m.name.toUpperCase(), Math.floor((w - 16) / 8.5)), "head");
      text(g, left, line + 16, cut(`${m.where.toUpperCase()}${rated}`, Math.floor(w / 6.5)), "dim");
      line += 42;
    }
    if (m.state === "working" && m.crate) {
      const c = m.crate;
      const crate = add(g, "g", { "data-crate": c.ticket || c.role });
      add(crate, "title", {}, `${c.ticket || c.role}: ${c.title || ""}`);
      add(crate, "rect", { x: left, y: line - 14, width: 44, height: 22, class: `crate ${c.kind}` });
      text(crate, left + 22, line + 1, c.ticket ? short(c.ticket) : "batch", "on", { "text-anchor": "middle" });
      text(g, left + 50, line + 1, `${c.minutes} min`, "name");
      text(g, left, line + 26, `attempt ${c.attempt}`, "dim");
    } else if (m.state === "waiting") {
      text(g, left, line, "limit reached", "name");
      text(g, left, line + 16, `resets ${m.reset}`, "dim");
    } else {
      text(g, left, line, m.state === "off" ? "off: no role" : m.stand_in ? "standing by" : "idle", "dim");
    }
    if (m.off.length) text(g, left, y + h - 8, cut(`off: ${m.off.join(", ")}`, Math.floor((w - 16) / 6.5)), "dim");
  }

  function machines(svg, doc) {
    for (const [name, area] of Object.entries(AREAS)) {
      const own = doc.machines.filter((m) => m.station === name);
      const g = station(svg, name);
      g.setAttribute("class", `station ${name}`);
      if (name === "reviewers") text(g, area.x + 2, area.y - 10, "REVIEWERS", "head");
      if (name === "developers") {
        add(g, "rect", { x: 548, y: 326, width: 430, height: 246, class: "unit", "stroke-dasharray": "8 5", "fill-opacity": 0.4 });
        text(g, 560, 346, "DEVELOPER BAY", "head");
      }
      if (!own.length) continue;
      const each = Math.min(area.most || area.width, (area.width - area.gap * (own.length - 1)) / own.length);
      own.forEach((m, i) => machine(g, m, area.x + i * (each + area.gap), area.y, each, area.height));
    }
  }

  // --- checks, merged, ripe, the stash ------------------------------------------------------

  function end(svg, doc, count) {
    const checks = station(svg, "checks");
    add(checks, "rect", { x: 982, y: 260, width: 74, height: 120, class: "unit" });
    add(checks, "circle", { cx: 1019, cy: 290, r: 10, class: "light" });
    text(checks, 1019, 322, "CHECKS", "head", { "text-anchor": "middle" });
    text(checks, 1019, 340, "ruff · mypy", "dim", { "text-anchor": "middle" });
    text(checks, 1019, 353, "tests · gates", "dim", { "text-anchor": "middle" });

    const merged = station(svg, "merged");
    add(merged, "rect", { x: 1120, y: 270, width: 186, height: 100, class: "unit" });
    text(merged, 1134, 292, `MERGED TODAY · ${count.merged}`, "head");
    doc.merged.slice(-6).forEach((crate, i) => {
      const x = 1134 + (i % 3) * 56, y = 304 + Math.floor(i / 3) * 28;
      const c = add(merged, "g", { "data-merged": crate.ticket });
      add(c, "title", {}, `${crate.ticket}: ${crate.title || ""}`);
      add(c, "rect", { x, y, width: 50, height: 22, class: `crate ${crate.kind}` });
      text(c, x + 25, y + 15, short(crate.ticket), "on", { "text-anchor": "middle" });
    });

    const ripe = station(svg, "ripe");
    add(ripe, "rect", { x: 1120, y: 84, width: 186, height: 130, class: "unit" });
    add(ripe, "circle", { cx: 1146, cy: 114, r: 12, class: "unit" });
    text(ripe, 1166, 112, `RIPE · ${count.ripe}`, "head big");
    text(ripe, 1166, 128, "needs your sign-off", "");
    doc.field.ripe.slice(0, 3).forEach((m, i) =>
      text(ripe, 1134, 156 + i * 18, cut(`${m.key.toUpperCase()} · ${m.title || ""}`, 24), "name"));

    const stash = station(svg, "stash");
    add(stash, "rect", { x: 1120, y: 420, width: 186, height: 190, class: "unit" });
    text(stash, 1134, 442, `HARVEST STASH · ${count.stash}`, "head");
    doc.field.stash.slice(0, 12).forEach((m, i) => {
      const x = 1134 + (i % 3) * 56, y = 456 + Math.floor(i / 3) * 30;
      add(stash, "rect", { x, y, width: 52, height: 26, class: "tile" });
      text(stash, x + 26, y + 17, m.key.toUpperCase(), "name", { "text-anchor": "middle" });
    });
    text(stash, 1134, 600, "latest first", "dim");
  }

  function draw(svg, doc) {
    svg.replaceChildren();
    const defs = add(svg, "defs");
    const soil = add(defs, "pattern", { id: "soil", width: 10, height: 10, patternUnits: "userSpaceOnUse" });
    add(soil, "path", { d: "M0 10L10 0", class: "soil-line" });
    const count = Object.fromEntries(doc.stations.map((s) => [s.id, s.count]));
    field(svg, doc, count);
    queue(svg, doc);
    machines(svg, doc);
    end(svg, doc, count);
    doc.belts.forEach((b) => belt(svg, b));  // over the units' edges, so every count shows
  }

  // --- phone: portrait floor under 640 px -----------------------------------------------

  const PHONE = {
    field:    { x: 6,  y: 8,  w: 346, h: 300 },
    queue:    { x: 60, y: 308, w: 238, h: 40 },
    lead:     { x: 6,  y: 358, w: 346, h: 118 },
    rev1:     { x: 6,  y: 486, w: 70,  h: 90 },
    rev2:     { x: 186, y: 486, w: 70,  h: 90 },
    bay:      { x: 8,  y: 606, w: 342, h: 160 },
    checks:   { x: 134, y: 806, w: 90,  h: 70 },
    merged:   { x: 14, y: 896, w: 160, h: 62 },
    ripe:     { x: 186, y: 896, w: 160, h: 62 },
    stash:    { x: 40, y: 986, w: 278, h: 86 },
  };

  function drawPhone(svg, doc) {
    svg.replaceChildren();
    const count = Object.fromEntries(doc.stations.map((s) => [s.id, s.count]));

    // field
    const field = add(svg, "g", { class: "station", "data-station": "seeds" });
    add(field, "rect", { x: PHONE.field.x, y: PHONE.field.y, width: PHONE.field.w, height: PHONE.field.h, class: "field-plot" });
    text(field, 16, 28, "THE FIELD", "head");
    const seeds = station(field, "seeds");
    add(seeds, "path", { d: `M${PHONE.field.x + 16} ${PHONE.field.y + 40} L${PHONE.field.x + 116} ${PHONE.field.y + 40} L${PHONE.field.x + 100} ${PHONE.field.y + 130} L${PHONE.field.x + 32} ${PHONE.field.y + 130} Z`, class: "unit" });
    text(seeds, 72, 158, "SEEDS", "head", { "text-anchor": "middle" });
    text(seeds, 72, 172, `${plural(count.seeds || 0, "ticket", "tickets")} set aside`, "dim", { "text-anchor": "middle" });

    // queue hopper
    const queue = station(svg, "queue");
    add(queue, "path", { d: `M${PHONE.queue.x} ${PHONE.queue.y} L${PHONE.queue.x + PHONE.queue.w} ${PHONE.queue.y} L${PHONE.queue.x + PHONE.queue.w - 18} ${PHONE.queue.y + PHONE.queue.h} L${PHONE.queue.x + 18} ${PHONE.queue.y + PHONE.queue.h} Z`, class: "unit" });
    text(queue, 179, PHONE.queue.y + 26, `QUEUE · ${doc.queue.length}`, "head", { "text-anchor": "middle" });

    // lead
    const lead = station(svg, "lead");
    const leadM = doc.machines.find((m) => m.station === "lead");
    if (leadM) {
      machine(lead, leadM, PHONE.lead.x, PHONE.lead.y, PHONE.lead.w, PHONE.lead.h);
    }

    // reviewers
    const revs = doc.machines.filter((m) => m.station === "reviewers");
    const revsStation = station(svg, "reviewers");
    revs.forEach((m, i) => {
      machine(revsStation, m, 6 + i * 180, PHONE.rev1.y, 70, PHONE.rev1.h);
    });

    // developer bay
    const bay = station(svg, "developers");
    add(bay, "rect", { x: PHONE.bay.x, y: PHONE.bay.y, width: PHONE.bay.w, height: PHONE.bay.h, class: "unit", "stroke-dasharray": "8 5", "fill-opacity": 0.4 });
    text(bay, 18, PHONE.bay.y + 20, "DEVELOPER BAY", "head");
    const devs = doc.machines.filter((m) => m.station === "developers");
    devs.forEach((m, i) => {
      const my = PHONE.bay.y + 30 + i * 100;
      machine(bay, m, 18 + i * 108, my, 104, 100);
    });

    // checks
    const checks = station(svg, "checks");
    add(checks, "rect", { x: PHONE.checks.x, y: PHONE.checks.y, width: PHONE.checks.w, height: PHONE.checks.h, class: "unit" });
    add(checks, "circle", { cx: PHONE.checks.x + 37, cy: PHONE.checks.y + 28, r: 10, class: "light" });
    text(checks, 179, PHONE.checks.y + 50, "CHECKS", "head", { "text-anchor": "middle" });

    // merged
    const merged = station(svg, "merged");
    add(merged, "rect", { x: PHONE.merged.x, y: PHONE.merged.y, width: PHONE.merged.w, height: PHONE.merged.h, class: "unit" });
    text(merged, 26, PHONE.merged.y + 22, `MERGED TODAY · ${count.merged || 0}`, "head");

    // ripe
    const ripe = station(svg, "ripe");
    add(ripe, "rect", { x: PHONE.ripe.x, y: PHONE.ripe.y, width: PHONE.ripe.w, height: PHONE.ripe.h, class: "unit" });
    add(ripe, "circle", { cx: PHONE.ripe.x + 12, cy: PHONE.ripe.y + 30, r: 12, class: "unit" });
    text(ripe, 198, PHONE.ripe.y + 30, `RIPE · ${count.ripe || 0}`, "head big");

    // stash
    const stash = station(svg, "stash");
    add(stash, "rect", { x: PHONE.stash.x, y: PHONE.stash.y, width: PHONE.stash.w, height: PHONE.stash.h, class: "unit", "stroke-dasharray": "6 4" });
    text(stash, 52, PHONE.stash.y + 20, `HARVEST STASH · ${count.stash || 0}`, "head");

    doc.belts.forEach((b) => belt(svg, b));
  }

  function drawAll(root) {
    const block = root.querySelector ? root.querySelector("#factory-line") : null;
    const svg = document.getElementById("floor");
    const phone = document.getElementById("floor-phone");
    if (block && svg && phone) {
      const narrow = window.innerWidth < 640;
      svg.style.display = narrow ? "none" : "block";
      phone.style.display = narrow ? "block" : "none";
      if (narrow) {
        drawPhone(phone, JSON.parse(block.textContent));
      } else {
        draw(svg, JSON.parse(block.textContent));
      }
      const doc = JSON.parse(block.textContent);
      const cur = {};
      for (const b of doc.belts) cur[b.id] = b.today || 0;
      const checks = cur["checks→merged"] || 0;
      const devs = cur["checks→developers"] || 0;
      const lead = cur["checks→lead"] || 0;
      const prev = _prev || {};
      const prevM = prev["checks→merged"] || 0;
      const prevD = prev["checks→developers"] || 0;
      const prevL = prev["checks→lead"] || 0;
      const light = svg.querySelector(".light");
      if (light && (checks > prevM || devs > prevD || lead > prevL)) {
        let cls = "light";
        if (checks > prevM) cls += " flash-green";
        else if (devs > prevD) cls += " flash-red";
        else if (lead > prevL) cls += " flash-orange";
        light.className.baseVal = cls;
      }
      _prev = cur;
    }
  }

  drawAll(document);
  document.addEventListener("htmx:load", (event) => drawAll(event.detail.elt));
})();
