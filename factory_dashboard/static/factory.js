// The factory line (f3 D11): draws svg#floor from the document in the JSON block
// #factory-line that line.py's live_line wrote. Every rule lives in that document; this only
// lays it out, as hand-written SVG after .softfield/cards/f3-line-mockup/Line.dc.html, coloured
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
  // A link from a crate carries the crate's own project (F132 D2), else the page's.
  const own_query = (project) => (project ? `?${new URLSearchParams({ project })}` : project_query());
  // F132 D9: with several projects on the floor a crate's label starts with its project's name.
  let manyProjects = false;  // the document drawn last says (`many_projects`)
  const plate = (crate) => (manyProjects && crate && crate.project ? `${crate.project} · ` : "");
  // A crate's name among its siblings: one ticket id can be in two projects
  const crateKey = (crate) => `${crate.project || ""}/${crate.ticket || crate.role}`;

  // `words` on lines of at most `n` characters, broken at its spaces.
  function wrap(words, n) {
    const lines = [];
    for (const word of words.split(" ")) {
      const last = lines.length - 1;
      if (last >= 0 && lines[last].length + 1 + word.length <= n) lines[last] += ` ${word}`;
      else lines.push(word);
    }
    return lines;
  }

  // The clog sign (f9-01): where the runner waits instead of working (the document's `wait`),
  // a warning triangle and what it waits for, from (x, y) on lines `width` wide; on a `plate`
  // where no unit is behind the words.
  function clog(parent, wait, x, y, width, plate = false) {
    const g = add(parent, "g", { class: "clog", "data-clog": wait.kind });
    add(g, "title", {}, wait.words);
    const lines = wrap(wait.words, Math.floor((width - 20) / 6.7));
    if (plate) add(g, "rect", { x: x - 6, y: y - 12, width: width + 12, height: lines.length * 12 + 7, class: "clog-plate" });
    add(g, "path", { d: `M${x + 7} ${y - 10} l7 12 h-14 Z`, class: "sign" });
    text(g, x + 7, y + 1, "!", "mark", { "text-anchor": "middle" });
    lines.forEach((words, n) => text(g, x + 20, y + n * 12, words, "clog-words"));
  }

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
  // A tap opens the card listing them (`showSeeds`), as a crate's does.
  function seeds(svg, doc, count, x, y, w, inside = false) {
    const g = station(svg, "seeds");
    g.setAttribute("data-seeds", "");
    g.setAttribute("tabindex", "0");
    g.setAttribute("role", "button");
    add(g, "title", {}, "Set-aside tickets");
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
    const query = project_query();
    const g = station(svg, "planting");
    const link = make_link(g, `/planning${query}`);
    const mid = x + w / 2;
    add(link, "rect", { x, y, width: w, height: h, class: "unit" });
    add(link, "rect", { x: x + w - 38, y: y - 34, width: 22, height: 34, class: "unit" });
    text(link, mid, y + 28, "PLANTING", "head", { "text-anchor": "middle" });
    text(link, mid, y + 46, "ideas you're planning", "", { "text-anchor": "middle" });
    text(link, mid, y + 60, "with the lead", "", { "text-anchor": "middle" });
    text(link, mid, y + 86, `${count.planting} in talks`, "dim", { "text-anchor": "middle" });
  }

  // The planted rows, the first four `step` apart, then how many tickets they feed `toward`.
  function rows(svg, doc, count, x, y, w, h, step, toward) {
    const g = station(svg, "rows");
    add(g, "rect", { x, y, width: w, height: h, class: "soil" });
    text(g, x + 10, y + 22, "PLANTED ROWS", "head");
    const bar = w - 64;
    doc.field.rows.slice(0, 4).forEach((row, n) => {
      const top = y + 54 + n * step, sx = x + 20, left = x + 40;
      const link = make_link(g, `/milestones/${row.key}${own_query(row.project)}`);
      add(link, "title", {}, `Go to ${plate(row)}${row.key.toUpperCase()} milestone`);
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
    const wait = doc.wait && doc.wait.station === "queue" ? doc.wait : null;
    if (wait) g.setAttribute("class", "station clogged");
    const mid = x + w / 2;
    add(g, "path", { d: `M${x} ${y} L${x + w} ${y} L${x + w - 18} ${y + h} L${x + 18} ${y + h} Z`, class: "unit" });
    text(g, mid, fit.inside ? y + 20 : y - 10, `QUEUE · ${doc.queue.length}`, "head", { "text-anchor": "middle" });
    const left = mid - (fit.cols * fit.pitch - (fit.pitch - fit.width)) / 2;
    // the clog's plate takes "in run order"'s place; inside the hopper, the upper rows' too
    if (wait && fit.inside) clog(g, wait, mid - 151, y + 35, 302, true);
    else if (wait) clog(g, wait, mid - 95, y + h + 20, 190, true);
    doc.queue.slice(0, wait && fit.inside ? fit.cols : fit.most).forEach((crate, i) => {
      const col = i % fit.cols, row = Math.floor(i / fit.cols);
      const cx = left + col * fit.pitch, cy = y + h - fit.bottom - row * fit.rise;
      // A due review (f4-20) is a batch crate: no ticket, its role names it
      const key = crate.ticket || crate.role;
      const c = add(g, "g", { "data-key": crateKey(crate), "data-queue-crate": key, "data-crate": key,
        "data-project": crate.project, tabindex: "0", role: "button" });
      const what = crate.ticket ? `${crate.ticket}: ${crate.title || ""}` : crate.title;
      add(c, "title", {}, `${plate(crate)}${crate.number} ${what}${crate.waits.length ? ` (after ${crate.waits.join(", ")})` : ""}`);
      add(c, "rect", { x: cx, y: cy, width: fit.width, height: 20, class: `crate ${crate.kind}${crate.waits.length ? " waits" : ""}` });
      text(c, cx + fit.width / 2, cy + 14, String(crate.number), "on", { "text-anchor": "middle" });
    });
    if (fit.inside) {
      if (!wait) text(g, mid, y + 38, "in run order", "dim", { "text-anchor": "middle" });
      return;
    }
    if (doc.queue.length > fit.most) text(g, mid, y + 22, `+ ${doc.queue.length - fit.most} more`, "dim", { "text-anchor": "middle" });
    if (!wait) text(g, mid, y + h + 20, "in run order", "dim", { "text-anchor": "middle" });
  }

  // --- the machines -------------------------------------------------------------------------

  const AREAS = {  // where each machine station's machines go, side by side; the bay's frame
    lead: { x: 560, y: 120, width: 230, height: 170, gap: 10 },
    reviewers: { x: 810, y: 50, width: 280, height: 112, gap: 10, most: 140 },
    developers: { x: 562, y: 404, width: 402, height: 108, gap: 12, most: 128, bay: { x: 548, y: 326, width: 430, height: 246 } },
  };

  // `wait`: the runner waits at this machine, which then stands still under the clog sign
  function machine(svg, m, x, y, w, h, wait = null) {
    const working = m.state === "working" && !wait;
    const cls = ["machine", m.station, m.state, m.stand_in ? "stand-in" : "", working ? "on" : "", m.state === "idle" ? "idle" : "", wait ? "clogged" : ""].filter(Boolean).join(" ");
    const g = add(svg, "g", { class: cls, "data-machine": m.id });
    add(g, "title", {}, `${m.name} · ${m.where} · ${wait ? wait.words : m.state}${m.rating !== "" ? ` · rated ${m.rating}` : ""}`);
    const tall = Math.round(30 * m.scale);
    if (m.station !== "reviewers") {
      add(g, "rect", { x: x + w - 34, y: y - tall, width: 18, height: tall, class: "unit" });
      if (working) {
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
    if (working) {  // three lights under the chimney, blinking in turn
      for (let k = 0; k < 3; k++) add(g, "rect", { x: x + w - 38 + k * 9, y: y + 6, width: 6, height: 4, class: "led" });
    }
    if (wait) {
      clog(g, wait, left, line, w - 20);
    } else if (working && m.crate) {
      const c = m.crate;
      const crate = add(g, "g", { "data-crate": c.ticket || c.role, "data-project": c.project,
        tabindex: "0", role: "button" });
      add(crate, "title", {}, `${plate(c)}${c.ticket || c.role}: ${c.title || ""}`);
      add(crate, "rect", { x: left, y: line - 14, width: 44, height: 22, class: `crate ${c.kind}` });
      text(crate, left + 22, line + 1, c.ticket ? short(c.ticket) : "batch", "on", { "text-anchor": "middle" });
      if (plate(c)) {  // its project beside it, the minutes on the attempt's line
        text(g, left + 50, line + 1, cut(c.project, Math.floor((w - 70) / 6.5)), "name", { "data-plate": c.project });
        text(g, left, line + 26, `attempt ${c.attempt} · ${c.minutes} min`, "dim");
      } else {
        text(g, left + 50, line + 1, `${c.minutes} min`, "name");
        text(g, left, line + 26, `attempt ${c.attempt}`, "dim");
      }
    } else if (m.state === "waiting") {
      text(g, left, line, "limit reached", "name");
      text(g, left, line + 16, `resets ${m.reset}`, "dim");
    } else if (m.state === "idle") {
      if (m.station === "lead" && m.next_ticket) {
        const link = make_link(g, `/tickets/${m.next_ticket}${own_query(m.next_project)}`);
        text(link, left, line, `next: ${short(m.next_ticket)}`, "dim");
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
      own.forEach((m, i) => machine(g, m, area.x + i * (each + area.gap), area.y, each, area.height,
        doc.wait && doc.wait.machine === m.id ? doc.wait : null));
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
      const c = add(g, "g", { "data-key": crateKey(crate), "data-merged": crate.ticket, "data-crate": crate.ticket,
        "data-project": crate.project, tabindex: "0", role: "button" });
      add(c, "title", {}, `${plate(crate)}${crate.ticket}: ${crate.title || ""}`);
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
    doc.field.ripe.slice(0, 3).forEach((m, i) => {
      const wrapper = add(g, "g", { "data-ripe": m.key });
      const link = make_link(wrapper, `/milestones/${m.key}${own_query(m.project)}`);
      text(link, x + 14, y + 72 + i * 18, cut(`${m.key.toUpperCase()} · ${m.title || ""}`, Math.floor((w - 28) / 7.2)), "name");
    });
  }

  // The harvest stash, latest first: `cols` tiles a row, as many rows as `h` holds.
  function stash(svg, doc, count, x, y, w, h, cols) {
    const g = station(svg, "stash");
    add(g, "rect", { x, y, width: w, height: h, class: "unit" });
    text(g, x + 14, y + 22, `HARVEST STASH · ${count.stash}`, "head");
    doc.field.stash.slice(0, cols * Math.floor((h - 60) / 30)).forEach((m, i) => {
      const tx = x + 14 + (i % cols) * 56, ty = y + 36 + Math.floor(i / cols) * 30;
      const tile = add(g, "g", { "data-stash": m.key });
      add(tile, "title", {}, `${plate(m)}${m.key.toUpperCase()}`);
      const link = make_link(tile, `/milestones/${m.key}${own_query(m.project)}`);
      add(link, "rect", { x: tx, y: ty, width: 52, height: 26, class: "tile" });
      text(link, tx + 26, ty + 17, m.key.split("-")[0].toUpperCase(), "name", { "text-anchor": "middle" });
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
    "queue→developers": { path: "M248 552 L350 552 L350 782 L183 782 L183 940", at: [196, 804], say: "developer" },
    "lead→checks": { path: "M26 700 L7 700 L7 1272 L134 1272", at: [14, 1322], say: "lead's work" },
    "developers→checks": { path: "M150 1156 L150 1196", at: [140, 1180], end: true },
    "checks→developers": { path: "M208 1196 L208 1156", at: [218, 1180], back: true, thin: true, short: true },
    "checks→lead": { path: "M134 1222 L19 1222 L19 740 L26 740", at: [30, 1212], back: true, thin: true, say: "back to the lead" },
    "checks→merged": { path: "M179 1306 L179 1336", at: [192, 1325] },
    "merged→ripe": { path: "M100 1432 L100 1462", at: [112, 1451] },
    "ripe→stash": { path: "M100 1582 L100 1612", at: [112, 1601] },
    "merged→reviewers": { path: "M340 1360 L351 1360 L351 868 L340 868", at: [338, 1252], end: true, back: true, thin: true, short: true },
  };

  // f9-27: the phone's planted rows, one line each: name, bar, "done/total". The busiest three
  // (running, then most ready) unless `open`; a toggle beside the footer shows or hides the
  // rest. Returns the station's height; the field and everything below shift by its difference
  // from the 262 the stations below were placed for.
  const PHONE_ROWS = { y: 176, shown: 3, step: 22, was: 262 };

  function phoneRows(svg, doc, count, open) {
    const all = [...doc.field.rows].sort((a, b) => (b.running - a.running) || (b.ready - a.ready));
    const list = open ? all : all.slice(0, PHONE_ROWS.shown);
    const x = 16, y = PHONE_ROWS.y, w = 326, h = 34 + Math.max(list.length, 1) * PHONE_ROWS.step + 20;
    const g = station(svg, "rows");
    add(g, "rect", { x, y, width: w, height: h, class: "soil" });
    text(g, x + 10, y + 22, "PLANTED ROWS", "head");
    list.forEach((row, n) => {
      const top = y + 40 + n * PHONE_ROWS.step;
      const link = make_link(g, `/milestones/${row.key}${own_query(row.project)}`);
      add(link, "title", {}, `Go to ${plate(row)}${row.key.toUpperCase()} milestone`);
      const r = add(link, "g", { "data-row": row.key });
      text(r, x + 10, top, cut(row.key.toUpperCase() + (row.title ? ` · ${row.title}` : ""), 16), "name");
      add(r, "rect", { x: x + 130, y: top - 8, width: 150, height: 7, class: "bar-bg" });
      add(r, "rect", { x: x + 130, y: top - 8, width: row.total ? (150 * row.done) / row.total : 0, height: 7, class: "bar-fill" });
      text(r, x + w - 10, top, `${row.done}/${row.total}`, "dim", { "text-anchor": "end" });
    });
    const queued = doc.field.rows.reduce((sum, row) => sum + row.ready, 0);
    text(g, x + 10, y + h - 12, `${plural(count.rows, "row feeds", "rows feed")} ${plural(queued, "ticket", "tickets")} ↓`, "dim");
    if (all.length > PHONE_ROWS.shown) {
      const t = add(g, "g", { "data-rows-toggle": "", tabindex: "0", role: "button" });
      add(t, "rect", { x: x + w - 104, y: y + h - 28, width: 94, height: 20, class: "tile" });
      text(t, x + w - 57, y + h - 14, open ? "Show fewer" : `Show all ${all.length}`, "name", { "text-anchor": "middle" });
    }
    return h;
  }

  let rowsOpen = false;  // the toggle's state, kept across the 5 s refresh

  function drawPhone(floor, doc) {
    const svg = document.createElementNS(NS, "svg");  // drawn aside, then morphed into `floor`
    soil(svg, "soil-phone");
    const count = Object.fromEntries(doc.stations.map((s) => [s.id, s.count]));
    const plot = add(svg, "rect", { x: 6, y: 8, class: "field-plot" });
    text(svg, 16, 28, "THE FIELD", "head");
    seeds(svg, doc, count, 16, 44, 150, true);
    planting(svg, count, 196, 48, 140, 98);
    const h = phoneRows(svg, doc, count, rowsOpen);
    const dy = h - PHONE_ROWS.was;  // what the rows gained (or lost) against the stations below
    plot.setAttribute("width", 346);
    plot.setAttribute("height", PHONE_ROWS.y + h);
    floor.setAttribute("viewBox", `0 0 358 ${PHONE_HEIGHT + dy}`);
    const top = ["seeds→planting", "planting→rows"];  // the belts that stay in the field
    doc.belts.filter((b) => top.includes(b.id)).forEach((b) => belt(svg, b, PHONE_BELTS));
    const below = add(svg, "g", { "data-below": "", transform: `translate(0 ${dy})` });
    queue(below, doc, 99, 492, 160, 100, PHONE_QUEUE);
    machines(below, doc, PHONE_AREAS);
    checks(below, 134, 1196, 90, 110);
    merged(below, doc, count, 26, 1336, 314, 96, 5);
    ripe(below, doc, count, 26, 1462, 314, 120);
    stash(below, doc, count, 26, 1612, 314, 120, 5);
    doc.belts.filter((b) => !top.includes(b.id)).forEach((b) => belt(below, b, PHONE_BELTS));
    morph(floor, svg);
  }

  // --- the map (F199): the whole factory from above on a 20-unit grid, one screen ------------
  // D3: geometry lives in these two tables and only here; a shape as wide as tall or wider takes
  // WIDE, else TALL. A zone is [x, y, w, h, name], a box [x, y, w, h], a belt [path, its
  // number's x and y, back]. D5: belts carry no words, only today's number when above zero.

  const WIDE = {
    w: 960, h: 540, statusY: 22,
    zones: { field: [16, 36, 228, 360, "THE FIELD"], lead: [452, 36, 214, 168, "THE LEAD"],
      reviewers: [716, 210, 88, 118, "REVIEWERS"], developers: [452, 300, 214, 168, "DEVELOPER BAY"] },
    seeds: [28, 66, 98, 76], planting: [134, 66, 98, 76],
    rows: { x: 28, y: 178, w: 204, h: 210, tile: 16, pitch: 18, head: 18, first: true },
    queue: { x: 284, y: 170, w: 124, h: 236, cols: 3, most: 15, crate: 28, pitch: 32, rise: 20 },
    machines: { lead: [460, 64, 198, 130], reviewers: [722, 236, 76, 86], developers: [460, 328, 198, 130] },
    most: 130,
    checks: [694, 56, 78, 104], merged: [812, 36, 132, 112], ripe: [812, 196, 132, 116], stash: [812, 360, 132, 164],
    legend: [16, 408, 228, 116],
    belts: {
      "seeds→planting": ["M126 104 H134"], "planting→rows": ["M183 142 V178"], "rows→queue": ["M232 290 H284"],
      "queue→lead": ["M408 230 H430 V120 H452", 430, 180], "queue→developers": ["M408 350 H452", 430, 350],
      "lead→checks": ["M666 90 H694", 680, 80], "checks→lead": ["M694 130 H666", 680, 120, true],
      "developers→checks": ["M666 400 H706 V160", 706, 300], "checks→developers": ["M694 150 H682 V350 H666", 682, 250, true],
      "checks→merged": ["M772 100 H812", 792, 100], "merged→ripe": ["M878 148 V196", 878, 172], "ripe→stash": ["M878 312 V360", 878, 336],
      "merged→reviewers": ["M830 148 V180 H760 V210", 790, 180, true],
    },
  };

  const TALL = {
    w: 360, h: 640, statusY: 14,
    zones: { field: [6, 22, 348, 106, "THE FIELD"], lead: [116, 136, 236, 106, "THE LEAD"],
      reviewers: [272, 262, 80, 112, "REVIEWERS"], developers: [116, 262, 136, 112, "DEVELOPER BAY"] },
    seeds: [12, 42, 58, 80], planting: [76, 42, 58, 80],
    rows: { x: 140, y: 42, w: 208, h: 82, tile: 10, pitch: 11.4, head: 14, first: false },
    queue: { x: 12, y: 146, w: 88, h: 92, cols: 3, most: 6, crate: 19, pitch: 20, rise: 17 },
    machines: { lead: [122, 158, 224, 78], reviewers: [277, 284, 70, 84], developers: [122, 284, 124, 84] },
    most: 124,
    checks: [134, 402, 100, 58], merged: [8, 500, 108, 124], ripe: [126, 500, 108, 124], stash: [244, 500, 108, 124],
    legend: null,  // f199-05: the key behind a "?"
    belts: {
      "seeds→planting": ["M70 82 H76"], "planting→rows": ["M134 82 H140"], "rows→queue": ["M56 128 V146"],
      "queue→lead": ["M100 190 H116", 108, 190], "queue→developers": ["M56 238 V318 H116", 56, 280],
      "lead→checks": ["M257 242 V425 H234", 257, 330], "checks→lead": ["M234 440 H267 V242", 267, 390, true],
      "developers→checks": ["M165 374 V402", 150, 388], "checks→developers": ["M205 402 V374", 220, 388, true],
      "checks→merged": ["M134 432 H62 V500", 62, 470], "merged→ripe": ["M116 562 H126", 121, 562], "ripe→stash": ["M234 562 H244", 239, 546],
      "merged→reviewers": ["M96 500 V480 H312 V374", 200, 480, true],
    },
  };

  const table = () => (window.innerWidth >= window.innerHeight ? WIDE : TALL);
  const CHAR = 6;  // a character's width at the map's 10 px mono, a little over for 9.5 px
  const mapStation = (svg, id, cls = "station") => add(svg, "g", { class: cls, "data-station": id });
  const cardKey = (key) => key.split("-")[0].toUpperCase();  // f7-line-polish → F7

  // The corner ticks: an ornament in the ink, never a status
  function ticks(g, x, y, w, h) {
    const s = 7;
    add(g, "path", { class: "tick", d: `M${x} ${y + s}V${y}H${x + s}M${x + w - s} ${y}H${x + w}V${y + s}M${x + w} ${y + h - s}V${y + h}H${x + w - s}M${x + s} ${y + h}H${x}V${y + h - s}` });
  }

  // A zone: a bay with ticks and a hazard plate naming it; the machines' zones are their stations
  function mapZone(svg, key, [x, y, w, h, name]) {
    const g = key === "field" ? add(svg, "g", { "data-zone": key }) : mapStation(svg, key);
    what(g, key);
    add(g, "rect", { x, y, width: w, height: h, class: "zone" });
    ticks(g, x, y, w, h);
    add(g, "path", { class: "plate-b", d: `M${x} ${y}H${x + name.length * 6.6 + 12}l-6 13H${x}Z` });
    text(g, x + 4, y + 10, name, "plate-t");
  }

  function mapBelt(svg, b, L) {
    const where = L.belts[b.id];
    if (!where) return;
    const cls = ["belt", where[3] ? "back" : "", b.today > 0 ? "today" : "", b.carrying ? "carrying" : ""].join(" ").trim();
    const g = add(svg, "g", { class: cls, "data-belt": b.id });
    add(g, "title", {}, b.label);
    add(g, "path", { d: where[0], class: "bed" });
    add(g, "path", { d: where[0], class: "rollers" });
  }

  // Today's numbers, over everything they sit by, so no unit covers one
  function chips(svg, doc, L) {
    const g = add(svg, "g", { "data-chips": "" });
    for (const b of doc.belts) {
      const where = L.belts[b.id];
      if (!where || where[1] === undefined || !(b.today > 0)) continue;
      const chip = add(g, "g", { "data-chip": b.id });
      const words = String(b.today), w = words.length * 6 + 6;
      add(chip, "rect", { x: where[1] - w / 2, y: where[2] - 6.5, width: w, height: 13, class: "chip" });
      text(chip, where[1], where[2] + 3, words, "chip-t", { "text-anchor": "middle" });
    }
  }

  // Seed and sprouting: a big number on a plot
  function plot(svg, id, [x, y, w, h], count, name) {
    const g = mapStation(svg, id);
    what(g, id);
    add(g, "rect", { x, y, width: w, height: h, class: "seedplot" });
    text(g, x + w / 2, y + h / 2 + 4, String(count), "num", { "text-anchor": "middle" });
    text(g, x + w / 2, y + h - 7, name, "dim", { "text-anchor": "middle" });
  }

  // D4: the planted cards, live; a replay's document has none, so its rows stand in
  function plantedCards(doc) {
    if (doc.field.planted) return doc.field.planted;
    return doc.field.rows.map((r) => ({ key: r.key, project: r.project, title: r.title, done: r.done,
      total: r.total, growing: r.running > 0 || r.done > 0, bug: r.key === "bugs" }));
  }

  // One tile per planted card, first top left: its merged tickets fill it from the bottom, a
  // ticket started edges it orange, a bug's edge is dashed. Tiles shrink when the cards outgrow P.
  function planted(svg, doc, count, P) {
    const g = mapStation(svg, "rows");
    what(g, "planted");
    add(g, "rect", { x: P.x, y: P.y, width: P.w, height: P.h, class: "plot" });
    text(g, P.x, P.y + 10, `PLANTED · ${count.rows}`, "title");
    const cards = plantedCards(doc);
    const room = P.h - P.head - (P.first ? 16 : 0);
    const height = (pitch) => Math.ceil(cards.length / Math.max(1, Math.floor(P.w / pitch))) * pitch;
    let pitch = P.pitch;
    while (pitch > 4 && height(pitch) > room) pitch -= 0.5;
    const size = (pitch * P.tile) / P.pitch, cols = Math.max(1, Math.floor(P.w / pitch));
    cards.forEach((card, i) => {
      const x = P.x + (i % cols) * pitch, y = P.y + P.head + Math.floor(i / cols) * pitch;
      const tile = add(g, "g", { "data-tile": `${card.project || ""}/${card.key}` });
      add(tile, "title", {}, `${plate(card)}${cardKey(card.key)}${card.title ? ` · ${card.title}` : ""} · ${card.done} of ${card.total} merged`);
      add(tile, "rect", { x, y, width: size, height: size, class: "tilebg" });
      const fill = card.total ? (size * card.done) / card.total : 0;
      if (fill) add(tile, "rect", { x, y: y + size - fill, width: size, height: fill, class: "tilefill" });
      add(tile, "rect", { x, y, width: size, height: size, class: `tileedge${card.growing ? " growing" : ""}${card.bug ? " bug" : ""}` });
    });
    if (P.first && cards.length) {
      const first = cards[0], at = P.y + P.head + Math.ceil(cards.length / cols) * pitch + 10;
      text(g, P.x, at, cut(`first in line: ${cardKey(first.key)}${first.title ? `, ${first.title}` : ""}`, Math.floor(P.w / CHAR)), "dim");
    }
  }

  // The queue's hopper, its count and its first crates in run order, from the bottom up; a wait
  // at the queue clogs it and signs it
  function mapQueue(svg, doc, Q, tall) {
    const wait = doc.wait && doc.wait.station === "queue";
    const g = mapStation(svg, "queue", wait ? "station clogged" : "station");
    what(g, "queue");
    add(g, "path", { class: "hopper", d: `M${Q.x} ${Q.y}H${Q.x + Q.w}L${Q.x + Q.w - 12} ${Q.y + Q.h}H${Q.x + 12}Z` });
    const mid = Q.x + Q.w / 2;
    text(g, mid, Q.y + (tall ? 12 : 16), "QUEUE", "title", { "text-anchor": "middle" });
    if (wait) add(g, "path", { class: "sign", d: `M${Q.x + 14} ${Q.y + (tall ? 4 : 7)} l6 11 h-12 Z` });
    text(g, mid, Q.y + (tall ? 34 : 46), String(doc.queue.length), tall ? "num small" : "num", { "text-anchor": "middle" });
    const left = Q.x + (Q.w - (Q.cols * Q.pitch - (Q.pitch - Q.crate))) / 2;
    doc.queue.slice(0, Q.most).forEach((crate, i) => {
      const cx = left + (i % Q.cols) * Q.pitch, cy = Q.y + Q.h - 4 - Q.rise * (Math.floor(i / Q.cols) + 1);
      const c = add(g, "g", { "data-key": `${crateKey(crate)}/${crate.milestone || ""}` });
      const what = crate.ticket ? `${crate.ticket}: ${crate.title || ""}` : crate.title;
      add(c, "title", {}, `${plate(crate)}${crate.number} ${what}${crate.waits.length ? ` (after ${crate.waits.join(", ")})` : ""}`);
      add(c, "rect", { x: cx, y: cy, width: Q.crate, height: Q.rise - 4, class: `crate ${crate.kind}${crate.waits.length ? " waits" : ""}` });
      text(c, cx + Q.crate / 2, cy + Q.rise - 8, String(crate.number), "on", { "text-anchor": "middle" });
    });
  }

  // A machine from above: its plate, a light, a vent where there's room; then what it does. Under
  // 56 units tall it keeps one line under its name. `wait`: the runner waits here, so it's clogged.
  function mapMachine(svg, m, x, y, w, h, wait) {
    const working = m.state === "working" && !wait;
    const cls = ["machine", m.station, wait ? "clogged" : m.state, m.stand_in ? "stand-in" : ""].filter(Boolean).join(" ");
    const g = add(svg, "g", { class: cls, "data-machine": m.id });
    g.classList.add("tap");
    add(g, "title", {}, `${m.name} · ${m.where} · ${wait ? wait.words : m.state}${m.rating !== "" ? ` · rated ${m.rating}` : ""}`);
    add(g, "path", { class: "unit", d: `M${x} ${y}H${x + w - 8}l8 8V${y + h}H${x}Z` });
    add(g, "rect", { x: x + 5, y: y + 5, width: 5, height: 5, class: "led" });
    const full = h >= 56, vent = full && w >= 90;
    if (vent) add(g, "circle", { cx: x + w - 15, cy: y + 19, r: Math.min(9, 6 + m.scale * 2), class: "vent" });
    const fits = (words, from) => cut(words, Math.floor((w - from - 4) / CHAR));
    text(g, x + 14, y + 11, cut(m.name.toUpperCase(), Math.floor((w - 14 - (vent ? 26 : 4)) / CHAR)), "nm");
    let line = y + Math.min(26, h - 6);
    if (full) {
      text(g, x + 5, y + 24, fits(`${m.local ? "local" : "cloud"}${m.rating !== "" ? ` · ${m.rating}` : ""}`, 5), "dim");
      line = y + (h < 100 ? 44 : 50);
    }
    const second = full && line + 16 <= y + h - 3;  // room for a line under it
    if (wait) {
      add(g, "path", { d: `M${x + 11} ${line - 9} l6 11 h-12 Z`, class: "sign" });
      const who = { claude: " Claude", owner: " you" }[wait.kind] || "";
      text(g, x + 22, line, fits(`waits for${who}`, 22), "nm");
      if (second && m.reset) text(g, x + 5, line + 16, fits(`reset ${m.reset}`, 5), "dim");
    } else if (working && m.crate) {
      const c = m.crate, what = c.ticket ? short(c.ticket) : "job";
      if (full) {
        add(g, "rect", { x: x + 5, y: line - 10, width: 40, height: 15, class: `crate ${c.kind}` });
        text(g, x + 25, line + 1, what, "on", { "text-anchor": "middle" });
        text(g, x + 49, line + 1, fits(`${c.minutes} min`, 49), "nm");
        if (second) text(g, x + 5, line + 16, fits(`${plate(c)}attempt ${c.attempt}`, 5), "dim");
      } else {
        add(g, "rect", { x: x + 5, y: line - 8, width: 8, height: 9, class: `crate ${c.kind}` });
        text(g, x + 17, line, fits(`${plate(c)}${what} · ${c.minutes} min`, 17), "nm");
      }
    } else {
      const words = m.state === "waiting" ? `limit · reset ${m.reset}` : m.state === "off" ? "off: no role" : m.stand_in ? "standby" : "idle";
      text(g, x + 5, line, fits(words, 5), "dim");
    }
  }

  // Each station's machines side by side while each is 90 wide, else one above the other
  function mapMachines(svg, doc, L) {
    for (const [name, [x, y, w, h]] of Object.entries(L.machines)) {
      const own = doc.machines.filter((m) => m.station === name);
      const n = own.length, gap = 6;
      const across = Math.min(L.most, (w - gap * (n - 1)) / n), down = (h - gap * (n - 1)) / n;
      own.forEach((m, i) => {
        const wait = doc.wait && doc.wait.machine === m.id ? doc.wait : null;
        if (n === 1 || across >= 90) mapMachine(svg, m, x + i * (across + gap), y, across, h, wait);
        else mapMachine(svg, m, x, y + i * (down + gap), w, down, wait);
      });
    }
  }

  // The checks: a gate with the light that flashes for each result
  function mapChecks(svg, [x, y, w, h], tall) {
    const g = mapStation(svg, "checks");
    what(g, "checks");
    add(g, "path", { class: "gate", d: `M${x} ${y + 8}l8 -8H${x + w - 8}l8 8V${y + h - 8}l-8 8H${x + 8}l-8 -8Z` });
    add(g, "circle", { cx: x + w / 2, cy: y + (tall ? 18 : 30), r: tall ? 8 : 11, class: "light" });
    text(g, x + w / 2, y + h - (tall ? 12 : 20), "CHECKS", "title", { "text-anchor": "middle" });
  }

  // Merged today, ripe and harvested: a box with its name and number, then what it holds
  function box(svg, id, [x, y, w, h], name, count, cls, draw = null) {
    const g = mapStation(svg, id);
    what(g, id);
    add(g, "rect", { x, y, width: w, height: h, class: cls });
    ticks(g, x, y, w, h);
    text(g, x + 7, y + 15, name, "title");
    text(g, x + 7, y + 42, String(count), "num");
    if (draw) draw(g, x, y, w, h, x + 7 + String(count).length * 15 + 8);
  }

  function boxes(svg, doc, count, L, tall) {
    box(svg, "merged", L.merged, "MERGED TODAY", count.merged, "unit");
    box(svg, "ripe", L.ripe, "RIPE", count.ripe, "ripebox", (g, x, y, w, h, after) => {
      text(g, after, y + 42, cut(tall ? "sign off" : "yours to sign off", Math.floor((x + w - after - 4) / CHAR)), "dim");
      doc.field.ripe.slice(0, Math.floor((h - 64) / 15)).forEach((m, i) =>
        text(g, x + 7, y + 60 + i * 15, cut(`${plate(m)}${cardKey(m.key)}${m.title ? ` · ${m.title}` : ""}`, Math.floor((w - 14) / CHAR)), "nm"));
    });
    box(svg, "stash", L.stash, "HARVESTED", count.stash, "unit", (g, x, y, w, h) => {
      const cols = 3, tw = (w - 14 - (cols - 1) * 3) / cols;
      doc.field.stash.slice(0, cols * Math.floor((h - 56) / 20)).forEach((m, i) => {
        const tx = x + 7 + (i % cols) * (tw + 3), ty = y + 52 + Math.floor(i / cols) * 20;
        add(g, "rect", { x: tx, y: ty, width: tw, height: 17, class: "seedplot" });
        text(g, tx + tw / 2, ty + 12, cut(cardKey(m.key), Math.floor(tw / 5.5)), "chip-t", { "text-anchor": "middle" });
      });
    });
  }

  // The key, on the wide map (a phone's comes behind a "?", f199-05)
  function legend(svg, [x, y, w, h]) {
    const g = add(svg, "g", { "data-legend": "" });
    add(g, "rect", { x, y, width: w, height: h, class: "zone" });
    ticks(g, x, y, w, h);
    text(g, x + 8, y + 16, "HOW TO READ IT", "title");
    [["lead", "lead ticket"], ["developer", "developer ticket"], ["batch", "review or planner job"]].forEach(([kind, words], i) => {
      add(g, "rect", { x: x + 8, y: y + 24 + i * 15, width: 14, height: 10, class: `crate ${kind}` });
      text(g, x + 28, y + 33 + i * 15, words);
    });
    add(g, "path", { d: `M${x + 8} ${y + 74}h14`, class: "swatch-line", stroke: "var(--roller)" });
    text(g, x + 28, y + 77, "belt carrying now");
    add(g, "path", { d: `M${x + 8} ${y + 89}h14`, class: "swatch-line", stroke: "var(--critical)", opacity: ".5" });
    text(g, x + 28, y + 92, "failed work coming back");
    text(g, x + 8, y + 107, "numbers: how many went that way today", "dim");
  }

  // What runs now, always at the top: the working machine, its crate and minutes; or the wait's
  // sign and words
  function mapStatus(svg, doc, L) {
    const g = add(svg, "g", { "data-status": doc.wait ? doc.wait.kind : "" });
    const most = Math.floor((L.w - 26) / 6.6);  // at 11 px
    if (doc.wait) {
      add(g, "path", { d: `M12 ${L.statusY - 9} l6 11 h-12 Z`, class: "sign" });
      text(g, 22, L.statusY, cut(doc.wait.words, most), "status");
      return;
    }
    const m = doc.machines.find((one) => one.state === "working" && one.crate);
    const c = m ? m.crate : null;
    const words = c ? `${m.name} · ${plate(c)}${c.ticket ? short(c.ticket) : c.title || c.role} · ${c.minutes} min` : "nothing is running";
    text(g, 8, L.statusY, cut(`NOW · ${words}`, most), "status");
  }

  const WHAT = {
    seeds: ["Seed", "65 ideas and set-aside tickets. A conversation with the lead plans them. On the page: opens the list."],
    sprouting: ["Sprouting", "8 cards being planned with the lead. On the page: opens the Planning room."],
    planted: ["Planted", "57 cards in line for the factory, in the board's order; 19 have a ticket started. On the page: opens this list, each card a link to its page."],
    queue: ["Queue", "105 tickets in run order. Faded, dashed crates wait for another ticket."],
    checks: ["Checks", "The runner's checks on each ticket's work: the light flashes green for a pass, red for a fail."],
    merged: ["Merged today", "Tickets whose work reached main today."],
    ripe: ["Ripe", "Every ticket done and the review written: yours to sign off. On the page: opens the review."],
    stash: ["Harvested", "65 cards signed off, the latest first."],
    legend: ["How to read the map", "Orange crate: a lead ticket. Blue crate: a developer ticket. Peach crate: a review or a planner job.\nYellow belt: carrying now. Faint yellow: work went this way today, and its number says how many. Thin red belt: failed work coming back.\nA tile is a planted card: yellow fill, its merged tickets; orange edge, a ticket started; dashed, a bug."],
  };

  const BELT_LABELS = {
    "seeds→planting": ["sprouting", "Cards move this way when you plan and approve them."],
    "planting→rows": ["planted", "Cards move this way when you plan and approve them."],
    "rows→queue": ["tickets", "Cards move this way when you plan and approve them."],
    "queue→lead": ["lead tickets", "Cards move this way when you plan and approve them."],
    "queue→developers": ["developer", "Cards move this way when you plan and approve them."],
    "lead→checks": ["lead's work", "Cards move this way when you plan and approve them."],
    "developers→checks": ["to checks", "Cards move this way when you plan and approve them."],
    "checks→developers": ["failed: retry", "Cards move this way when you plan and approve them."],
    "checks→lead": ["failed twice: direction · 3×: escalation", "Cards move this way when you plan and approve them."],
    "checks→merged": ["merged", "Cards move this way when you plan and approve them."],
    "merged→ripe": ["ripened", "Cards move this way when you plan and approve them."],
    "ripe→stash": ["your sign-off", "Cards move this way when you plan and approve them."],
    "merged→reviewers": ["checkpoints", "Cards move this way when you plan and approve them."],
  };

  // A zone, station or plot that a tap opens the card for: marks it and records what to show.
  function what(g, key) { g.setAttribute("data-what", key); g.classList.add("tap"); }

  function drawMap(map, doc, L) {
    map.setAttribute("viewBox", `0 0 ${L.w} ${L.h}`);
    const svg = document.createElementNS(NS, "svg");  // drawn aside, then morphed into `map`
    const tall = L === TALL;
    const count = Object.fromEntries(doc.stations.map((s) => [s.id, s.count]));
    const grid = add(add(svg, "defs"), "pattern", { id: "map-grid", width: 20, height: 20, patternUnits: "userSpaceOnUse" });
    add(grid, "path", { d: "M20 0V20H0", class: "gridline" });
    add(svg, "rect", { x: 0, y: 0, width: L.w, height: L.h, class: "ground" });
    add(svg, "rect", { x: 0, y: 0, width: L.w, height: L.h, fill: "url(#map-grid)" });
    for (const [key, zone] of Object.entries(L.zones)) mapZone(svg, key, zone);
    doc.belts.forEach((b) => mapBelt(svg, b, L));
    plot(svg, "seeds", L.seeds, count.seeds, "SEED");
    plot(svg, "planting", L.planting, count.planting, "SPROUTING");
    planted(svg, doc, count, L.rows);
    mapQueue(svg, doc, L.queue, tall);
    mapMachines(svg, doc, L);
    mapChecks(svg, L.checks, tall);
    boxes(svg, doc, count, L, tall);
    if (L.legend) legend(svg, L.legend);
    chips(svg, doc, L);
    mapStatus(svg, doc, L);
    morph(map, svg);
  }

  const narrow = () => window.innerWidth < 640;
  // the floor drawn: the map, on its page; else the Overview's phone or wide floor
  const shown = () => document.getElementById("map") || document.getElementById(narrow() ? "floor-phone" : "floor");

  let shownDoc = null;  // the document the floor last drew, live or replayed: the card's
  let cardCrate = null;  // the crate the card shows; null: closed. A redraw shows it again
  const SEEDS = Symbol("seeds");  // as `cardCrate`: the card lists the set-aside tickets
  let mapCardKey = null;  // the map element the card shows; null: closed. A redraw shows it again

  // svg#map when the page has one (F199); else the Overview's two floors, one shown
  function drawFloor(doc) {
    manyProjects = Boolean(doc.many_projects);
    const map = document.getElementById("map");
    if (map) {
      drawMap(map, doc, table());
    } else {
      const svg = document.getElementById("floor");
      const phone = document.getElementById("floor-phone");
      svg.style.display = narrow() ? "none" : "block";
      phone.style.display = narrow() ? "block" : "none";
      if (narrow()) drawPhone(phone, doc);
      else draw(svg, doc);
    }
    shownDoc = doc;
    if (cardCrate === SEEDS) showSeeds();
    else if (cardCrate) showCard(cardCrate.key, cardCrate.project);
    if (mapCardKey) showMapCard(mapCardKey, doc);
  }

  let drawn = null;  // the live document last drawn, and on which floor; null: draw it again

  function toggleRows() {  // f9-27: the phone's planted rows, three or all
    rowsOpen = !rowsOpen;
    drawn = null;
    if (shownDoc) drawFloor(shownDoc);
  }

  function drawAll(root) {
    const block = root.querySelector ? root.querySelector("#factory-line") : null;
    const map = document.getElementById("map");
    const floors = document.getElementById("floor") && document.getElementById("floor-phone");
    if (replaying || !(block && (map || floors))) return;  // a replay holds the floor
    const doc = JSON.parse(block.textContent);
    // `at` alone draws nothing; a phone turned draws the other floor, or the map's other table
    const shape = map ? table() === WIDE : narrow();
    const now = JSON.stringify([Boolean(map), shape, rowsOpen, { ...doc, at: null }]);
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
  // have it after the event. `crates` remembers each crate's {ticket, project, title, kind} and
  // attempts, by `crateKey`: a ticket id is unique only inside its project (F132 D9).
  function apply(doc, event, crates) {
    if (event.at.slice(0, 10) !== doc.at.slice(0, 10)) {  // past midnight: today's counts restart
      doc.belts.forEach((b) => { if (b.today !== null) b.today = 0; });
      doc.merged = [];
    }
    doc.at = event.at;
    if (event.kind === "trip") {
      const moved = { ticket: event.crate, project: event.project };
      const crate = crates[crateKey(moved)] || { ...moved, title: null, kind: "developer" };
      doc.queue = doc.queue.filter((c) => crateKey(c) !== crateKey(moved));
      if (event.to === "queue") doc.queue.unshift({ ...crate, milestone: null, waits: [] });
      if (event.to === "merged") doc.merged.push({ ticket: crate.ticket, project: crate.project, title: crate.title, kind: crate.kind });
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
      const on = { ticket: event.ticket, project: event.project };
      if (!event.ticket) {
        m.crate = null;
      } else if (!m.crate || crateKey(m.crate) !== crateKey(on)) {
        const crate = crates[crateKey(on)] || { ...on, title: null, kind: "developer" };
        crate.attempt = (crate.attempt || 0) + 1;
        crates[crateKey(on)] = crate;
        m.crate = { ticket: crate.ticket, project: crate.project, title: crate.title, kind: crate.kind, role: null, attempt: crate.attempt, minutes: 0 };
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
      return `${clock} ${plate(event)}${event.crate} ${to}`;
    }
    if (event.kind === "check") {
      return `${clock} ${plate(event)}${event.crate} ${event.passed ? "passed checks" : `failed checks${event.gate ? `: ${event.gate}` : ""}`}`;
    }
    if (event.kind === "machine") {
      if (event.state === "working") return `${clock} ${event.machine} works on ${plate(event)}${event.ticket}`;
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
    for (const c of [...doc.queue, ...doc.merged]) crates[crateKey(c)] = { ticket: c.ticket, project: c.project, title: c.title, kind: c.kind };
    for (const m of doc.machines) {
      if (!m.crate) continue;
      if (m.crate.ticket) crates[crateKey(m.crate)] = { ...m.crate };
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
      const newAway = document.createElement("div");
      newAway.innerHTML = await awayResp.text();
      const oldAway = document.getElementById("away");
      if (oldAway) oldAway.replaceWith(...newAway.childNodes);
    }
  });
  document.getElementById("replay-live")?.addEventListener("click", backToLive);
  document.getElementById("replay-play")?.addEventListener("click", play);
  document.getElementById("replay-prev")?.addEventListener("click", () => { stop(); show(step - 1); });
  document.getElementById("replay-next")?.addEventListener("click", () => { stop(); show(step + 1); });

  // --- crate card (f3-19): click a crate to see its details -------------------------------
  // Built from nodes and text, never HTML: a title, an id or the page's ?project= could hold
  // markup (f3 review, f3-F1). It reads the document the floor last drew, live or replayed.

  function crateInfo(doc, key, project) {
    // a batch: its role; the same id in another project is another crate
    const own = (c) => (c.ticket === key || (!c.ticket && c.role === key)) && (!project || c.project === project);
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

  function showCard(key, project = null) {
    const card = document.getElementById("crate-card");
    if (!card || !key || !shownDoc) return;
    const info = crateInfo(shownDoc, key, project);
    if (!info) return;
    cardCrate = { key, project };
    const parts = [];
    if (plate(info)) parts.push(el("span", "proj", info.project));  // whose crate (F132 D3)
    if (info.ticket) {
      const link = el("a", "card-ticket", info.ticket);
      link.setAttribute("href", `/tickets/${encodeURIComponent(info.ticket)}${own_query(info.project)}`);
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
    fillCard(card, parts);
  }

  function fillCard(card, parts) {
    card.replaceChildren(...parts);
    // Close button on phone (f9-24)
    if (narrow()) {
      const close = el("button", "card-close", "Close");
      close.addEventListener("click", () => hideCard());
      card.append(close);
    }
    card.hidden = false;
  }

  // The seeds' card (f9-25): every set-aside ticket as a link, then the Tickets page's list.
  function showSeeds() {
    const card = document.getElementById("crate-card");
    if (!card || !shownDoc) return;
    cardCrate = SEEDS;
    const query = project_query();
    const list = el("ul", "card-list");
    for (const seed of shownDoc.field.later || []) {
      const item = el("li");
      if (plate(seed)) item.append(el("span", "proj", seed.project));
      const link = el("a", "card-ticket", seed.ticket);
      link.setAttribute("href", `/tickets/${encodeURIComponent(seed.ticket)}${own_query(seed.project)}`);
      item.append(link);
      if (seed.title) item.append(el("span", "card-title", seed.title));
      list.append(item);
    }
    const all = el("a", "card-all", "All set-aside tickets");
    all.setAttribute("href", `/tickets${query}#later`);
    fillCard(card, [el("div", "card-head", `${plural(list.children.length, "ticket", "tickets")} set aside`), list, all]);
  }

  function hideCard() {
    const card = document.getElementById("crate-card");
    if (card) card.hidden = true;
    cardCrate = null;
  }

  // The map card (F199-04): a tap on anything on the map says what it is, in plain words,
  // and links to where it lives. Built from nodes and text, never HTML.
  function showMapCard(key, doc) {
    const card = document.getElementById("map-card");
    if (!card || !key || !doc) return;
    mapCardKey = key;
    const parts = [];
    if (key === "queue") {
      const [title, words] = ["Queue", `${doc.queue.length} tickets in run order. Faded, dashed crates wait for another ticket.`];
      const a = document.createElement("a");
      a.className = "card-all";
      a.href = "/queue";
      a.textContent = "The whole queue ›";
      parts.push(el("div", "card-head", title), el("div", "card-words", words), a);
    } else if (key === "planted") {
      const cards = doc.field.planted || [];
      const head = el("div", "card-head", `${plural(cards.length, "card", "cards")} planted`);
      parts.push(head);
      const list = el("ul", "card-list");
      for (const card of cards) {
        const item = el("li");
        if (plate(card)) item.append(el("span", "proj", card.project));
        const link = el("a", "card-ticket", card.key);
        link.setAttribute("href", `/milestones/${encodeURIComponent(card.key)}${own_query(card.project)}`);
        item.append(link);
        if (card.title) item.append(el("span", "card-title", card.title));
        list.append(item);
      }
      parts.push(list);
    } else if (key in WHAT) {
      const [title, words] = WHAT[key];
      parts.push(el("div", "card-head", title));
      parts.push(el("div", "card-words", words));
    } else if (key === "checks") {
      const [title, words] = ["Checks", "The runner's checks on each ticket's work: the light flashes green for a pass, red for a fail."];
      parts.push(el("div", "card-head", title), el("div", "card-words", words));
    } else if (key === "merged") {
      const [title, words] = ["Merged today", "Tickets whose work reached main today."];
      parts.push(el("div", "card-head", title), el("div", "card-words", words));
    } else if (key === "ripe") {
      const [title, words] = ["Ripe", "Every ticket done and the review written: yours to sign off."];
      parts.push(el("div", "card-head", title), el("div", "card-words", words));
    } else if (key === "stash") {
      const [title, words] = ["Harvested", "Cards signed off, the latest first."];
      parts.push(el("div", "card-head", title), el("div", "card-words", words));
    } else if (key === "legend") {
      const [title, words] = ["How to read the map", "Orange crate: a lead ticket. Blue crate: a developer ticket.\nA tile is a planted card: yellow fill its merged tickets; orange edge a ticket started."];
      parts.push(el("div", "card-head", title), el("div", "card-words", words));
    } else {
      const m = doc.machines.find((one) => one.id === key);
      if (!m) return;
      const title = m.name;
      const rating = m.rating !== "" ? `rated ${m.rating}` : "not rated yet";
      const station = m.station === "developers" ? "the developer bay" : m.station === "lead" ? "the lead" : "reviewers";
      const working = m.state === "working" && m.crate;
      const on = working ? `${m.crate.ticket || "job"} · ${m.crate.minutes} min` : m.state;
      const parts2 = [el("div", "card-head", title), el("div", "card-words", `${m.where}, ${rating}. Station: ${station}. On the page: its crate, and a link to the agent.`)];
      if (working) {
        parts2.push(meta([["on", on], ["station", station]]));
      }
      parts.push(...parts2);
    }
    fillMapCard(card, parts);
  }

  function fillMapCard(card, parts) {
    card.replaceChildren(...parts);
    card.hidden = false;
  }

  function hideMapCard() {
    const card = document.getElementById("map-card");
    if (card) card.hidden = true;
    mapCardKey = null;
  }

  // One listener on the floor wrapper finds the [data-crate] (merged crates included) clicked
  document.addEventListener("click", (e) => {
    const crate = e.target.closest("[data-crate]");
    if (crate) { showCard(crate.dataset.crate, crate.dataset.project); return; }  // a merged crate is a [data-crate] too
    if (e.target.closest("[data-seeds]")) { showSeeds(); return; }
    if (e.target.closest("[data-rows-toggle]")) { toggleRows(); return; }
    const w = e.target.closest("[data-what]");
    if (w) { showMapCard(w.dataset.what, shownDoc); return; }
    const mapCard = document.getElementById("map-card");
    if (mapCard && !mapCard.hidden && !mapCard.contains(e.target)) hideMapCard();
    const card = document.getElementById("crate-card");
    if (card && !card.hidden && !card.contains(e.target)) hideCard();
  });

  // Keyboard: Enter opens, Escape closes
  document.addEventListener("keydown", (e) => {
    const card = document.getElementById("crate-card");
    if (e.key === "Escape" && card && !card.hidden) { hideCard(); return; }
    const mapCard = document.getElementById("map-card");
    if (e.key === "Escape" && mapCard && !mapCard.hidden) { hideMapCard(); return; }
    if (e.key !== "Enter") return;
    const crate = e.target.closest("[data-crate]");
    if (crate) { e.preventDefault(); showCard(crate.dataset.crate, crate.dataset.project); }
    if (e.target.closest("[data-seeds]")) { e.preventDefault(); showSeeds(); }
    if (e.target.closest("[data-rows-toggle]")) { e.preventDefault(); toggleRows(); }
    const w = e.target.closest("[data-what]");
    if (w) { e.preventDefault(); showMapCard(w.dataset.what, shownDoc); }
  });

  drawAll(document);
  document.addEventListener("htmx:load", (event) => drawAll(event.detail.elt));
})();
