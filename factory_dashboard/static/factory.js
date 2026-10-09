// The factory line (f3 D11): draws svg#floor from the document in the JSON block
// #factory-line that line.py's live_line wrote. Every rule lives in that document; this only
// lays it out, as hand-written SVG after docs/milestones/f3-line-mockup/Line.dc.html, coloured
// by the stylesheet's tokens. Every 5 s htmx fetches the document alone (f3-17); when it
// differs, the floor is drawn again in place: a node whose part didn't change stays the same
// node, so its animation runs on.
"use strict";

(() => {
  const NS = "http://www.w3.org/2000/svg";

  // A node's name among its siblings: its first data-* attribute; null: matched by tag, in order.
  function key(node) {
    for (const a of node.attributes) if (a.name.startsWith("data-")) return `${a.name}=${a.value}`;
    return null;
  }

  // Gives `old` the children of `fresh` (a scratch drawing), keeping every old node that has a
  // match: by its key, else the next of its tag. Kept nodes never move, so nothing restarts.
  function morph(old, fresh) {
    const named = new Map(), loose = [];
    for (const child of old.children) {
      const k = key(child);
      if (k) named.set(k, child);
      else loose.push(child);
    }
    const kids = [...fresh.children].map((next) => {
      const k = key(next);
      let was = null;
      if (k) {
        was = named.get(k) || null;
        named.delete(k);
      } else {
        const n = loose.findIndex((c) => c.tagName === next.tagName);
        if (n >= 0) was = loose.splice(n, 1)[0];
      }
      if (!was || was.tagName !== next.tagName) return next;
      sync(was, next);
      return was;
    });
    const keep = new Set(kids);
    for (const child of [...old.children]) if (!keep.has(child)) child.remove();
    kids.forEach((kid, n) => { if (old.children[n] !== kid) old.insertBefore(kid, old.children[n] || null); });
  }

  function sync(old, fresh) {
    for (const a of [...old.attributes]) if (!fresh.hasAttribute(a.name)) old.removeAttribute(a.name);
    for (const a of fresh.attributes) if (old.getAttribute(a.name) !== a.value) old.setAttribute(a.name, a.value);
    if (old.children.length || fresh.children.length) morph(old, fresh);
    else if (old.textContent !== fresh.textContent) old.textContent = fresh.textContent;
  }

  // The checks light's flash, started again even when the light flashed the same way before.
  function flash(light, cls) {
    light.className.baseVal = "light";
    light.getBoundingClientRect();  // the style without the flash, so the next one starts over
    light.className.baseVal = `light ${cls}`;
  }

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
  const make_link = (svg, href) => add(svg, "a", { href, tabindex: "0", role: "link" });
  const project_query = () => {
    const project = new URLSearchParams(window.location.search).get("project");
    return project ? `?${new URLSearchParams({ project })}` : "";
  };

  // --- the belts: where each D11 belt runs, and where its words go -------------------------

  let _prev = null;  // the checks' counts last drawn; null until the first draw sets them

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

  // `say`: shorter words for the phone, where the long ones don't fit; the title keeps them
  function belt(svg, b, belts = BELTS) {
    const where = belts[b.id];
    if (!where) return;
    const cls = ["belt", where.back ? "back" : "", b.today > 0 ? "today" : "", b.carrying ? "carrying" : "", b.carrying ? "moving" : ""].join(" ").trim();
    const g = add(svg, "g", { class: cls, "data-belt": b.id });
    add(g, "title", {}, b.label);
    const width = where.thin ? 10 : 13;
    add(g, "path", { d: where.path, class: "bed", "stroke-width": width + 5 });
    add(g, "path", { d: where.path, class: "rollers", "stroke-width": width });
    const label = where.say || b.label;
    const words = b.today === null ? (where.short ? "" : label) : where.short ? `${b.today} today` : `${label} · ${b.today} today`;
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

  // The seeds' hopper, `w` wide at its top; its words go under it, or `inside` its top.
  function seeds(svg, doc, count, x, y, w, inside = false) {
    const query = project_query();
    const link = make_link(svg, `/tickets${query}#later`);
    add(link, "title", {}, "Set aside tickets");
    const g = station(link, "seeds");
    const h = 106, mid = x + w / 2;
    add(g, "path", { d: `M${x} ${y} L${x + w} ${y} L${x + w - 18} ${y + h} L${x + 18} ${y + h} Z`, class: "unit" });
    const spots = [[-15, 80], [3, 88], [19, 78], [-5, 66], [13, 60], [-23, 66], [27, 64], [5, 50]];
    spots.slice(0, Math.min(doc.field.seeds, spots.length)).forEach(([dx, dy]) =>
      add(g, "ellipse", { cx: mid + dx, cy: y + dy, rx: 7, ry: 5, class: "seed" }));
    const at = inside ? y + 18 : y + h + 20;
    text(g, mid, at, "SEEDS", "head", { "text-anchor": "middle" });
    text(g, mid, at + 16, `${plural(count.seeds, "ticket", "tickets")} set aside`, "dim", { "text-anchor": "middle" });
  }

  function planting(svg, count, x, y, w, h) {
    const g = station(svg, "planting");
    const mid = x + w / 2;
    add(g, "rect", { x, y, width: w, height: h, class: "unit" });
    add(g, "rect", { x: x + w - 38, y: y - 34, width: 22, height: 34, class: "unit" });
    text(g, mid, y + 28, "PLANTING", "head", { "text-anchor": "middle" });
    text(g, mid, y + 46, "ideas you're planning", "", { "text-anchor": "middle" });
    text(g, mid, y + 60, "with the lead", "", { "text-anchor": "middle" });
    text(g, mid, y + 86, `${count.planting} in talks`, "dim", { "text-anchor": "middle" });
  }

  // The planted rows, the first four `step` apart, then how many tickets they feed `toward`.
  function rows(svg, doc, count, x, y, w, h, step, toward) {
    const g = station(svg, "rows");
    add(g, "rect", { x, y, width: w, height: h, class: "soil" });
    text(g, x + 10, y + 22, "PLANTED ROWS", "head");
    const bar = w - 64;
    doc.field.rows.slice(0, 4).forEach((row, n) => {
      const top = y + 54 + n * step, sx = x + 20, left = x + 40;
      const query = project_query();
      const link = make_link(g, `/milestones/${row.key}${query}`);
      add(link, "title", {}, `Go to ${row.key.toUpperCase()} milestone`);
      const r = add(link, "g", { "data-row": row.key });
      add(r, "path", { class: "sprout", d: `M${sx} ${top + 14} v-22 M${sx} ${top + 2} c-8 0-11-4-11-9 8 0 11 4 11 9 M${sx} ${top - 2} c0-7 3-10 10-10 0 7-3 10-10 10 ` });
      text(r, left, top - 2, cut(row.title ? `${row.key.toUpperCase()} · ${row.title}` : row.key.toUpperCase(), Math.floor((w - 50) / 7.2)), "name");
      add(r, "rect", { x: left, y: top + 6, width: bar, height: 7, class: "bar-bg" });
      add(r, "rect", { x: left, y: top + 6, width: row.total ? (bar * row.done) / row.total : 0, height: 7, class: "bar-fill" });
      const running = row.running ? ` · ${row.running} running` : "";
      text(r, left, top + 28, `${row.done} of ${row.total} merged · ${row.ready} ready${running}`, "dim");
    });
    const more = doc.field.rows.length > 4 ? `+ ${doc.field.rows.length - 4} more · ` : "";
    const queued = doc.field.rows.reduce((sum, row) => sum + row.ready, 0);
    text(g, x + 10, y + h - 10, `${more}${plural(count.rows, "row feeds", "rows feed")} ${plural(queued, "ticket", "tickets")} ${toward}`, "dim");
  }

  function field(svg, doc, count) {
    add(svg, "rect", { x: 12, y: 34, width: 300, height: 590, class: "field-plot" });
    text(svg, 26, 56, "THE FIELD", "head");
    seeds(svg, doc, count, 40, 90, 110);
    planting(svg, count, 176, 92, 124, 104);
    rows(svg, doc, count, 30, 262, 264, 300, 58, "→");
  }

  // --- the queue ----------------------------------------------------------------------------

  // The queue's hopper and its first `fit.most` crates in run order, `fit.cols` a row from the
  // bottom up; its head over the hopper, or inside it when `fit.inside`.
  const QUEUE = { cols: 2, most: 16, width: 34, pitch: 38, rise: 22, bottom: 40, inside: false };

  function queue(svg, doc, x, y, w, h, fit = QUEUE) {
    const g = station(svg, "queue");
    const mid = x + w / 2;
    add(g, "path", { d: `M${x} ${y} L${x + w} ${y} L${x + w - 18} ${y + h} L${x + 18} ${y + h} Z`, class: "unit" });
    text(g, mid, fit.inside ? y + 20 : y - 10, `QUEUE · ${doc.queue.length}`, "head", { "text-anchor": "middle" });
    const left = mid - (fit.cols * fit.pitch - (fit.pitch - fit.width)) / 2;
    doc.queue.slice(0, fit.most).forEach((crate, i) => {
      const col = i % fit.cols, row = Math.floor(i / fit.cols);
      const cx = left + col * fit.pitch, cy = y + h - fit.bottom - row * fit.rise;
      // A due review (f4-20) is a batch crate: no ticket, its role names it
      const key = crate.ticket || crate.role;
      const c = add(g, "g", { "data-queue-crate": key, "data-crate": key,
        tabindex: "0", role: "button" });
      const what = crate.ticket ? `${crate.ticket}: ${crate.title || ""}` : crate.title;
      add(c, "title", {}, `${crate.number} ${what}${crate.waits.length ? ` (after ${crate.waits.join(", ")})` : ""}`);
      add(c, "rect", { x: cx, y: cy, width: fit.width, height: 20, class: `crate ${crate.kind}${crate.waits.length ? " waits" : ""}` });
      text(c, cx + fit.width / 2, cy + 14, String(crate.number), "on", { "text-anchor": "middle" });
    });
    if (fit.inside) {
      text(g, mid, y + 38, "in run order", "dim", { "text-anchor": "middle" });
      return;
    }
    if (doc.queue.length > fit.most) text(g, mid, y + 22, `+ ${doc.queue.length - fit.most} more`, "dim", { "text-anchor": "middle" });
    text(g, mid, y + h + 20, "in run order", "dim", { "text-anchor": "middle" });
  }

  // --- the machines -------------------------------------------------------------------------

  const AREAS = {  // where each machine station's machines go, side by side; the bay's frame
    lead: { x: 560, y: 120, width: 230, height: 170, gap: 10 },
    reviewers: { x: 810, y: 50, width: 280, height: 112, gap: 10, most: 140 },
    developers: { x: 562, y: 404, width: 402, height: 108, gap: 12, most: 128, bay: { x: 548, y: 326, width: 430, height: 246 } },
  };

  function machine(svg, m, x, y, w, h) {
    const cls = ["machine", m.station, m.state, m.stand_in ? "stand-in" : "", m.state === "working" ? "on" : "", m.state === "idle" ? "idle" : ""].join(" ").trim();
    const g = add(svg, "g", { class: cls, "data-machine": m.id });
    add(g, "title", {}, `${m.name} · ${m.where} · ${m.state}${m.rating !== "" ? ` · rated ${m.rating}` : ""}`);
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
    const rated = m.rating !== "" ? ` · ${m.rating}` : "";
    if (m.station === "lead") {
      text(g, left + 5, y + 25, "THE LEAD", "head big");
      add(g, "rect", { x: left + 5, y: y + 38, width: w - 30, height: 28, class: "plate" });
      text(g, left + 5 + (w - 30) / 2, y + 57, `${m.name.toUpperCase()}${rated}`, "on", { "text-anchor": "middle" });
      line = y + 88;
    } else {
      text(g, left, line, cut(m.name.toUpperCase(), Math.floor((w - 16) / 8.5)), "head");
      // its plate: solid for the local GPU, outlined for a cloud, sized to its words
      const wh = m.where === "local GPU" ? "local" : "cloud";
      const words = cut(`${m.where.toUpperCase()}${m.rating !== "" ? rated : " · not rated yet"}`, Math.floor((w - 24) / 4.6));
      add(g, "rect", { x: left, y: line + 7, width: Math.min(w - 20, words.length * 5 + 12), height: 14, class: `plate ${wh}` });
      text(g, left + 6, line + 17.5, words, `ptext ${wh}`);
      line += 42;
    }
    if (m.state === "working") {  // three lights under the chimney, blinking in turn
      for (let k = 0; k < 3; k++) add(g, "rect", { x: x + w - 38 + k * 9, y: y + 6, width: 6, height: 4, class: "led" });
    }
    if (m.state === "working" && m.crate) {
      const c = m.crate;
      const crate = add(g, "g", { "data-crate": c.ticket || c.role,
        tabindex: "0", role: "button" });
      add(crate, "title", {}, `${c.ticket || c.role}: ${c.title || ""}`);
      add(crate, "rect", { x: left, y: line - 14, width: 44, height: 22, class: `crate ${c.kind}` });
      text(crate, left + 22, line + 1, c.ticket ? short(c.ticket) : "batch", "on", { "text-anchor": "middle" });
      text(g, left + 50, line + 1, `${c.minutes} min`, "name");
      text(g, left, line + 26, `attempt ${c.attempt}`, "dim");
    } else if (m.state === "waiting") {
      text(g, left, line, "limit reached", "name");
      text(g, left, line + 16, `resets ${m.reset}`, "dim");
    } else if (m.state === "idle") {
      if (m.station === "lead" && m.next_ticket) {
        text(g, left, line, `next: ${short(m.next_ticket)}`, "dim");
        if (m.merged_today && m.merged_today > 0) {
          text(g, left, line + 16, `${m.merged_today} merged today`, "dim");
        }
      } else {
        text(g, left, line, m.stand_in ? "standing by" : "idle", "dim");
        if (m.merged_today && m.merged_today > 0) {
          text(g, left, line + 16, `${m.merged_today} merged today`, "dim");
        }
      }
    } else {
      text(g, left, line, m.state === "off" ? "off: no role" : m.stand_in ? "standing by" : "idle", "dim");
    }
    if (m.off.length) text(g, left, y + h - 8, cut(`off: ${m.off.join(", ")}`, Math.floor((w - 16) / 6.5)), "dim");
  }

  function machines(svg, doc, areas = AREAS) {
    for (const [name, area] of Object.entries(areas)) {
      const own = doc.machines.filter((m) => m.station === name);
      const g = station(svg, name);
      g.setAttribute("class", `station ${name}`);
      if (name === "reviewers") text(g, area.x + 2, area.y - 10, "REVIEWERS", "head");
      if (area.bay) {
        const { x, y, width, height } = area.bay;
        add(g, "rect", { x, y, width, height, class: "unit", "stroke-dasharray": "8 5", "fill-opacity": 0.4 });
        text(g, x + 12, y + 20, "DEVELOPER BAY", "head");
      }
      if (!own.length) continue;
      const each = Math.min(area.most || area.width, (area.width - area.gap * (own.length - 1)) / own.length);
      own.forEach((m, i) => machine(g, m, area.x + i * (each + area.gap), area.y, each, area.height));
    }
  }

  // --- checks, merged, ripe, the stash ------------------------------------------------------

  function checks(svg, x, y, w, h) {
    const g = station(svg, "checks");
    const mid = x + w / 2;
    add(g, "rect", { x, y, width: w, height: h, class: "unit" });
    add(g, "circle", { cx: mid, cy: y + 30, r: 10, class: "light" });
    text(g, mid, y + 62, "CHECKS", "head", { "text-anchor": "middle" });
    text(g, mid, y + 79, "ruff · mypy", "dim", { "text-anchor": "middle" });
    text(g, mid, y + 95, "tests · gates", "dim", { "text-anchor": "middle" });  // f5-14's font is taller
  }

  function merged(svg, doc, count, x, y, w, h, cols) {
    const g = station(svg, "merged");
    add(g, "rect", { x, y, width: w, height: h, class: "unit" });
    text(g, x + 14, y + 22, `MERGED TODAY · ${count.merged}`, "head");
    doc.merged.slice(-6).forEach((crate, i) => {
      const cx = x + 14 + (i % cols) * 56, cy = y + 34 + Math.floor(i / cols) * 28;
      const c = add(g, "g", { "data-merged": crate.ticket });
      add(c, "title", {}, `${crate.ticket}: ${crate.title || ""}`);
      add(c, "rect", { x: cx, y: cy, width: 50, height: 22, class: `crate ${crate.kind}` });
      text(c, cx + 25, cy + 15, short(crate.ticket), "on", { "text-anchor": "middle" });
    });
  }

  function ripe(svg, doc, count, x, y, w, h) {
    const g = station(svg, "ripe");
    add(g, "rect", { x, y, width: w, height: h, class: "unit" });
    add(g, "circle", { cx: x + 26, cy: y + 30, r: 12, class: "unit" });
    text(g, x + 46, y + 28, `RIPE · ${count.ripe}`, "head big");
    text(g, x + 46, y + 44, "needs your sign-off", "");
    doc.field.ripe.slice(0, 3).forEach((m, i) =>
      text(g, x + 14, y + 72 + i * 18, cut(`${m.key.toUpperCase()} · ${m.title || ""}`, Math.floor((w - 28) / 7.2)), "name", { "data-ripe": m.key }));
  }

  // The harvest stash, latest first: `cols` tiles a row, as many rows as `h` holds.
  function stash(svg, doc, count, x, y, w, h, cols) {
    const g = station(svg, "stash");
    add(g, "rect", { x, y, width: w, height: h, class: "unit" });
    text(g, x + 14, y + 22, `HARVEST STASH · ${count.stash}`, "head");
    doc.field.stash.slice(0, cols * Math.floor((h - 60) / 30)).forEach((m, i) => {
      const tx = x + 14 + (i % cols) * 56, ty = y + 36 + Math.floor(i / cols) * 30;
      const tile = add(g, "g", { "data-stash": m.key });
      add(tile, "rect", { x: tx, y: ty, width: 52, height: 26, class: "tile" });
      text(tile, tx + 26, ty + 17, m.key.toUpperCase(), "name", { "text-anchor": "middle" });
    });
    text(g, x + 14, y + h - 10, "latest first", "dim");
  }

  function end(svg, doc, count) {
    checks(svg, 982, 260, 74, 120);
    merged(svg, doc, count, 1120, 270, 186, 100, 3);
    ripe(svg, doc, count, 1120, 84, 186, 130);
    stash(svg, doc, count, 1120, 420, 186, 190, 3);
  }

  function soil(svg, id) {
    const defs = add(svg, "defs");
    const pattern = add(defs, "pattern", { id, width: 10, height: 10, patternUnits: "userSpaceOnUse" });
    add(pattern, "path", { d: "M0 10L10 0", class: "soil-line" });
  }

  function draw(floor, doc) {
    const svg = document.createElementNS(NS, "svg");  // drawn aside, then morphed into `floor`
    soil(svg, "soil");
    const count = Object.fromEntries(doc.stations.map((s) => [s.id, s.count]));
    field(svg, doc, count);
    queue(svg, doc, 360, 330, 110, 230);
    machines(svg, doc);
    end(svg, doc, count);
    doc.belts.forEach((b) => belt(svg, b));  // over the units' edges, so every count shows
    morph(floor, svg);
  }

  // --- phone: the same stations top to bottom, under 640 px (LinePhone.dc.html) ------------
  // Belts that skip stations run in the gutters: lead→checks and checks→lead on the left,
  // queue→developers then merged→reviewers on the right; the developers' belt comes down
  // between the two reviewers.

  const PHONE_HEIGHT = 1740;

  const PHONE_QUEUE = { cols: 3, most: 6, width: 30, pitch: 33, rise: 24, bottom: 30, inside: true };

  const PHONE_AREAS = {
    lead: { x: 26, y: 630, width: 314, height: 140, gap: 0 },
    reviewers: { x: 26, y: 812, width: 314, height: 112, gap: 22, most: 146 },
    developers: { x: 36, y: 1032, width: 294, height: 112, gap: 8, most: 146, bay: { x: 26, y: 940, width: 314, height: 216 } },
  };

  const PHONE_BELTS = {
    "seeds→planting": { path: "M158 92 L196 92", at: [177, 82], middle: true, short: true },
    "planting→rows": { path: "M266 146 L266 176", at: [278, 166] },
    "rows→queue": { path: "M179 438 L179 492", at: [192, 470] },
    "queue→lead": { path: "M125 592 L125 630", at: [114, 614], end: true, short: true },
    "queue→developers": { path: "M248 552 L350 552 L350 782 L183 782 L183 940", at: [262, 540], say: "developer", short: true },
    "lead→checks": { path: "M26 700 L7 700 L7 1272 L134 1272", at: [30, 1262], say: "lead's work", short: true },
    "developers→checks": { path: "M150 1156 L150 1196", at: [140, 1180], end: true },
    "checks→developers": { path: "M208 1196 L208 1156", at: [218, 1180], back: true, thin: true, short: true },
    "checks→lead": { path: "M134 1222 L19 1222 L19 740 L26 740", at: [30, 1212], back: true, thin: true, say: "back to the lead", short: true },
    "checks→merged": { path: "M179 1306 L179 1336", at: [192, 1325], short: true },
    "merged→ripe": { path: "M100 1432 L100 1462", at: [112, 1451] },
    "ripe→stash": { path: "M100 1582 L100 1612", at: [112, 1601] },
    "merged→reviewers": { path: "M340 1360 L351 1360 L351 868 L340 868", at: [338, 1252], end: true, back: true, thin: true, short: true },
  };

  function drawPhone(floor, doc) {
    floor.setAttribute("viewBox", `0 0 358 ${PHONE_HEIGHT}`);
    const svg = document.createElementNS(NS, "svg");  // drawn aside, then morphed into `floor`
    soil(svg, "soil-phone");
    const count = Object.fromEntries(doc.stations.map((s) => [s.id, s.count]));
    add(svg, "rect", { x: 6, y: 8, width: 346, height: 438, class: "field-plot" });
    text(svg, 16, 28, "THE FIELD", "head");
    seeds(svg, doc, count, 16, 44, 150, true);
    planting(svg, count, 196, 48, 140, 98);
    rows(svg, doc, count, 16, 176, 326, 262, 50, "↓");
    queue(svg, doc, 99, 492, 160, 100, PHONE_QUEUE);
    machines(svg, doc, PHONE_AREAS);
    checks(svg, 134, 1196, 90, 110);
    merged(svg, doc, count, 26, 1336, 314, 96, 5);
    ripe(svg, doc, count, 26, 1462, 314, 120);
    stash(svg, doc, count, 26, 1612, 314, 120, 5);
    doc.belts.forEach((b) => belt(svg, b, PHONE_BELTS));
    morph(floor, svg);
  }

  const narrow = () => window.innerWidth < 640;
  const shown = () => document.getElementById(narrow() ? "floor-phone" : "floor");

  let shownDoc = null;  // the document the floor last drew, live or replayed: the card's
  let cardCrate = null;  // the crate the card shows; null: closed. A redraw shows it again

  function drawFloor(doc) {
    const svg = document.getElementById("floor");
    const phone = document.getElementById("floor-phone");
    svg.style.display = narrow() ? "none" : "block";
    phone.style.display = narrow() ? "block" : "none";
    if (narrow()) drawPhone(phone, doc);
    else draw(svg, doc);
    shownDoc = doc;
    if (cardCrate) showCard(cardCrate);
  }

  let drawn = null;  // the live document last drawn, and on which floor; null: draw it again

  function drawAll(root) {
    const block = root.querySelector ? root.querySelector("#factory-line") : null;
    const svg = document.getElementById("floor");
    const phone = document.getElementById("floor-phone");
    if (replaying || !(block && svg && phone)) return;  // a replay holds the floor
    const doc = JSON.parse(block.textContent);
    const now = JSON.stringify([narrow(), { ...doc, at: null }]);  // `at` alone draws nothing
    if (now === drawn) return;
    drawn = now;
    drawFloor(doc);
    const cur = {};
    for (const b of doc.belts) cur[b.id] = b.today || 0;
    const prev = _prev;
    _prev = cur;
    if (!prev) return;  // the first draw: today's counts so far are no news
    const light = shown().querySelector(".light");
    if (!light) return;
    if (cur["checks→merged"] > prev["checks→merged"]) flash(light, "flash-green");
    else if (cur["checks→developers"] > prev["checks→developers"]) flash(light, "flash-red");
    else if (cur["checks→lead"] > prev["checks→lead"]) flash(light, "flash-orange");
  }

  // --- replay (f3-07): the floor as it was at `since`; f3-11 steps through `replaying.events`

  let replaying = null;  // /line/replay's {since, until, line, events} while replaying
  let step = 0;  // how many of replaying.events the floor shows
  let playing = null;  // Play's timer

  // One event applied to the document `doc` (a copy of replaying.line), as live_line would
  // have it after the event. `crates` remembers each crate's {ticket, title, kind} and attempts.
  function apply(doc, event, crates) {
    if (event.at.slice(0, 10) !== doc.at.slice(0, 10)) {  // past midnight: today's counts restart
      doc.belts.forEach((b) => { if (b.today !== null) b.today = 0; });
      doc.merged = [];
    }
    doc.at = event.at;
    if (event.kind === "trip") {
      const crate = crates[event.crate] || { ticket: event.crate, title: null, kind: "developer" };
      doc.queue = doc.queue.filter((c) => c.ticket !== event.crate);
      if (event.to === "queue") doc.queue.unshift({ ...crate, milestone: null, waits: [] });
      if (event.to === "merged") doc.merged.push({ ticket: crate.ticket, title: crate.title, kind: crate.kind });
      doc.queue.forEach((c, n) => { c.number = n + 1; });
      doc.belts.forEach((b) => {
        b.carrying = event.belts.includes(b.id);
        if (b.carrying && b.today !== null) b.today += 1;
      });
    } else if (event.kind === "machine") {
      const m = doc.machines.find((one) => one.id === event.machine);
      if (!m) return;
      m.state = event.state;
      m.reset = event.reset;
      if (!event.ticket) {
        m.crate = null;
      } else if (m.crate?.ticket !== event.ticket) {
        const crate = crates[event.ticket] || { ticket: event.ticket, title: null, kind: "developer" };
        crate.attempt = (crate.attempt || 0) + 1;
        crates[event.ticket] = crate;
        m.crate = { ticket: crate.ticket, title: crate.title, kind: crate.kind, role: null, attempt: crate.attempt, minutes: 0 };
        m.started = Date.parse(event.at);
      }
    }
    doc.machines.forEach((m) => {  // a working crate's minutes run on with the clock
      if (m.crate && m.started !== undefined) m.crate.minutes = Math.floor((Date.parse(event.at) - m.started) / 60000);
    });
    const count = { queue: doc.queue.length, merged: doc.merged.length };
    doc.stations.forEach((s) => { if (s.id in count) s.count = count[s.id]; });
  }

  // The event in words, after its own clock (the `at` string's, never the browser's zone).
  function words(event) {
    const clock = event.at.slice(11, 16);
    if (event.kind === "trip") {
      const to = event.to === null ? "leaves the line" : event.to === "queue" ? "goes back to the queue" : `goes to ${event.to}`;
      return `${clock} ${event.crate} ${to}`;
    }
    if (event.kind === "check") {
      return `${clock} ${event.crate} ${event.passed ? "passed checks" : `failed checks${event.gate ? `: ${event.gate}` : ""}`}`;
    }
    if (event.kind === "machine") {
      if (event.state === "working") return `${clock} ${event.machine} works on ${event.ticket}`;
      if (event.state === "waiting") return `${clock} ${event.machine} waits for its limit, resets ${event.reset}`;
      return `${clock} ${event.machine} is ${event.state}`;
    }
    if (event.kind === "limit") {
      return `${clock} ${event.agent} ${event.state === "start" ? "reached its limit" : "is past its limit"}`;
    }
    if (event.kind === "card") {
      return `${clock} ${event.card} ${event.stage ? `moves to ${event.stage}` : "leaves the field"}`;
    }
    return `${clock} nothing works for ${event.minutes} min`;
  }

  // The floor after the first n events, its readout, and the checks light for a check.
  function show(n) {
    step = Math.max(0, Math.min(n, replaying.events.length));
    const doc = structuredClone(replaying.line);  // replaying.line stays as it came, for ◀
    const crates = {};
    for (const c of [...doc.queue, ...doc.merged]) crates[c.ticket] = { ticket: c.ticket, title: c.title, kind: c.kind };
    for (const m of doc.machines) {
      if (!m.crate) continue;
      if (m.crate.ticket) crates[m.crate.ticket] = { ...m.crate };
      m.started = Date.parse(doc.at) - m.crate.minutes * 60000;
    }
    replaying.events.slice(0, step).forEach((event) => apply(doc, event, crates));
    drawFloor(doc);
    const readout = document.getElementById("replay-readout");
    if (step === 0) {
      const clock = replaying.since.slice(11, 16);  // the server's own clock, not the browser's
      readout.textContent = `${plural(replaying.events.length, "event", "events")} since ${clock}`;
      return;
    }
    const event = replaying.events[step - 1];
    readout.textContent = words(event);
    if (event.kind === "check") {
      const light = shown().querySelector(".light");
      if (light) flash(light, event.passed ? "flash-green" : "flash-red");
    }
  }

  function stop() {
    clearTimeout(playing);
    playing = null;
    document.getElementById("replay-play").textContent = "Play";
  }

  function tick() {
    show(step + 1);
    if (step >= replaying.events.length) return stop();
    playing = setTimeout(tick, Number(document.getElementById("replay-speed").value));
  }

  function play() {
    if (playing) return stop();
    if (step >= replaying.events.length) show(0);
    document.getElementById("replay-play").textContent = "Pause";
    playing = setTimeout(tick, Number(document.getElementById("replay-speed").value));
  }

  async function startReplay() {
    // the chosen span's replay: choosing another reloads the page with its ?since= (f3-21)
    const page = document.querySelector(".page[data-replay]");
    const response = await fetch(page.dataset.replay, { headers: { Accept: "application/json" } });
    if (!response.ok) return;
    stop();
    replaying = await response.json();
    show(0);
    document.getElementById("replay-controls").hidden = false;
    document.getElementById("replay").classList.add("replaying");
  }

  function backToLive() {
    stop();
    replaying = null;
    document.getElementById("replay-controls").hidden = true;
    document.getElementById("replay").classList.remove("replaying");
    drawn = null;  // the floor shows the replay's
    drawAll(document);
  }

  document.addEventListener("htmx:beforeRequest", (event) => {
    if (replaying && event.target.id === "line-live") event.preventDefault();  // paused
  });
  // The 5 s refresh's document: kept in the block, drawn unless a replay holds the floor.
  document.addEventListener("htmx:afterRequest", (event) => {
    if (event.target.id !== "line-live" || !event.detail.successful) return;
    document.getElementById("factory-line").textContent = event.detail.xhr.responseText;
    drawAll(document);
  });
  addEventListener("resize", () => drawAll(document));  // a phone turned: the other floor
  document.getElementById("replay-start")?.addEventListener("click", startReplay);
  document.getElementById("replay-span")?.addEventListener("change", async (e) => {
    const url = e.target.value;
    const parsed = new URL(url, window.location.origin);
    const since = parsed.searchParams.get("since");
    if (!since) return;
    // Update the address bar without reloading (f9-14).
    window.history.pushState({ since }, "", `?since=${encodeURIComponent(since)}`);
    // Update the page's data attributes for replay.
    const page = document.querySelector(".page[data-since]");
    if (page) {
      page.dataset.since = since;
      page.dataset.replay = `/line/replay?since=${encodeURIComponent(since)}`;
    }
    // Swap the away section in place.
    const awayResp = await fetch(`/away?since=${encodeURIComponent(since)}`);
    if (awayResp.ok) {
      document.getElementById("away").innerHTML = await awayResp.text();
    }
  });
  document.getElementById("replay-live")?.addEventListener("click", backToLive);
  document.getElementById("replay-play")?.addEventListener("click", play);
  document.getElementById("replay-prev")?.addEventListener("click", () => { stop(); show(step - 1); });
  document.getElementById("replay-next")?.addEventListener("click", () => { stop(); show(step + 1); });

  // --- crate card (f3-19): click a crate to see its details -------------------------------
  // Built from nodes and text, never HTML: a title, an id or the page's ?project= could hold
  // markup (f3 review, f3-F1). It reads the document the floor last drew, live or replayed.

  function crateInfo(doc, key) {
    const own = (c) => c.ticket === key || (!c.ticket && c.role === key);  // a batch: its role
    for (const c of doc.queue) if (own(c)) return { ...c, _source: "queue" };
    for (const m of doc.machines) if (m.crate && own(m.crate)) return { ...m.crate, _source: "machine", _agent: m.name };
    for (const c of doc.merged) if (own(c)) return { ...c, _source: "merged" };
    return null;
  }

  function el(tag, cls, words = null) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (words !== null) node.textContent = String(words);
    return node;
  }

  function meta(pairs) {
    const dl = el("dl", "card-meta");
    for (const [term, value] of pairs) dl.append(el("dt", "", term), el("dd", "", value));
    return dl;
  }

  function showCard(key) {
    const card = document.getElementById("crate-card");
    if (!card || !key || !shownDoc) return;
    const info = crateInfo(shownDoc, key);
    if (!info) return;
    cardCrate = key;
    const parts = [];
    if (info.ticket) {
      const project = new URLSearchParams(window.location.search).get("project");
      const link = el("a", "card-ticket", info.ticket);
      const query = project ? `?${new URLSearchParams({ project })}` : "";
      link.setAttribute("href", `/tickets/${encodeURIComponent(info.ticket)}${query}`);
      parts.push(link);
      if (info.title) parts.push(el("div", "card-title", info.title));
      if (info.kind === "lead" || info.kind === "developer") parts.push(meta([["role", info.kind]]));
      if (info._source === "machine" && info._agent) {
        parts.push(meta([["agent", info._agent], ["attempt", info.attempt], ["time", `${info.minutes} min`]]));
      }
      if (info.waits && info.waits.length) parts.push(el("div", "card-waits", info.waits.join(", ")));
    } else {
      parts.push(el("span", "card-ticket", info.role || "batch"));
      if (info.title) parts.push(el("div", "card-title", info.title));
    }
    card.replaceChildren(...parts);
    card.hidden = false;
  }

  function hideCard() {
    const card = document.getElementById("crate-card");
    if (card) card.hidden = true;
    cardCrate = null;
  }

  // One listener on the floor wrapper finds the [data-crate] clicked
  document.addEventListener("click", (e) => {
    const crate = e.target.closest("[data-crate]");
    if (crate) { showCard(crate.dataset.crate); return; }
    const card = document.getElementById("crate-card");
    if (card && !card.hidden && !card.contains(e.target) && !e.target.closest("[data-crate]")) hideCard();
  });

  // Keyboard: Enter opens, Escape closes
  document.addEventListener("keydown", (e) => {
    const card = document.getElementById("crate-card");
    if (e.key === "Escape" && card && !card.hidden) { hideCard(); return; }
    if (e.key !== "Enter") return;
    const crate = e.target.closest("[data-crate]");
    if (crate) { e.preventDefault(); showCard(crate.dataset.crate); }
  });

  drawAll(document);
  document.addEventListener("htmx:load", (event) => drawAll(event.detail.elt));
})();
