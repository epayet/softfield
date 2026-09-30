// The dashboard's charts (f1 D5). A page writes <div data-chart="<kind>"> followed by a
// <script type="application/json"> data block; this draws it with ECharts, using the function
// of that kind below. Tests check the JSON a route renders, not the drawing.
"use strict";

(() => {
  // The stylesheet's colours, so charts follow light and dark mode.
  function colours() {
    const css = getComputedStyle(document.documentElement);
    const get = (name) => css.getPropertyValue(name).trim();
    return {
      ink: get("--ink-2"), muted: get("--muted"), grid: get("--grid"), rule: get("--rule"),
      series: [get("--a2"), get("--a1"), get("--a3"), get("--a4"), get("--a7")],
      font: get("--sans"),
    };
  }

  const dollars = (value) => `$${value.toFixed(2)}`;

  // One function per kind: (data, colours) -> ECharts option.
  const kinds = {
    // Claude's dollars per milestone, oldest first: {labels: [...], dollars: [...]}.
    spend(data, c) {
      return {
        grid: { left: 48, right: 12, top: 16, bottom: 24 },
        tooltip: { trigger: "axis", valueFormatter: dollars },
        xAxis: {
          type: "category", data: data.labels,
          axisLine: { lineStyle: { color: c.rule } }, axisLabel: { color: c.ink },
        },
        yAxis: {
          type: "value", axisLabel: { color: c.muted, formatter: (v) => `$${v}` },
          splitLine: { lineStyle: { color: c.grid } },
        },
        series: [{
          name: "Claude", type: "bar", data: data.dollars, barMaxWidth: 36,
          itemStyle: { color: c.series[0], borderRadius: [3, 3, 0, 0] },
        }],
      };
    },
  };

  function draw(root) {
    for (const el of root.querySelectorAll("[data-chart]")) {
      const option = kinds[el.dataset.chart];
      const block = el.nextElementSibling;
      if (!option || !block || el.dataset.drawn) continue;
      const chart = echarts.init(el, null, { renderer: "svg" });
      const c = colours();
      chart.setOption({ textStyle: { fontFamily: c.font }, ...option(JSON.parse(block.textContent), c) });
      el.dataset.drawn = "1";
      new ResizeObserver(() => chart.resize()).observe(el);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    draw(document);
    // Partials htmx swaps in may hold charts too.
    document.body.addEventListener("htmx:afterSwap", (event) => draw(event.target));
  });
})();
