// The board's field (F15 D2): under 900 px one stage shows at a time, the planted one at first
// or the one the address names (#stage-ripe), and a press on a plot shows its stage. From
// 900 px dashboard.css shows every stage whatever is picked, so a plot is only a count there.
// Without this script every stage shows, stacked.
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
})();
