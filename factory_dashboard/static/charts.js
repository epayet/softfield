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

  function outcomeColor(outcome) {
    const colors = {
      passed: '#2ecc71',
      failed: '#e74c3c',
      timeout: '#f39c12',
      running: '#3498db',
      refused: '#9b59b6',
    };
    return colors[outcome] || '#95a5a6';
  }

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

    // First-attempt pass rate per milestone: {labels: [...], rate: [...]}.
    "milestone-rate"(data, c) {
      return {
        grid: { left: 48, right: 12, top: 16, bottom: 24 },
        tooltip: { trigger: "axis", valueFormatter: (v) => v == null ? "–" : v + "%" },
        xAxis: {
          type: "category", data: data.labels,
          axisLine: { lineStyle: { color: c.rule } }, axisLabel: { color: c.ink },
        },
        yAxis: {
          type: "value", axisLabel: { color: c.muted, formatter: (v) => v + "%" },
          splitLine: { lineStyle: { color: c.grid } },
        },
        series: [{
          name: "Rate", type: "bar", data: data.rate, barMaxWidth: 36,
          itemStyle: { color: c.series[2], borderRadius: [3, 3, 0, 0] },
        }],
      };
    },

    // Escalations per milestone: {labels: [...], count: [...]}.
    "milestone-esc"(data, c) {
      return {
        grid: { left: 48, right: 12, top: 16, bottom: 24 },
        tooltip: { trigger: "axis", valueFormatter: (v) => v },
        xAxis: {
          type: "category", data: data.labels,
          axisLine: { lineStyle: { color: c.rule } }, axisLabel: { color: c.ink },
        },
        yAxis: {
          type: "value", axisLabel: { color: c.muted },
          splitLine: { lineStyle: { color: c.grid } },
        },
        series: [{
          name: "Escalations", type: "bar", data: data.count, barMaxWidth: 36,
          itemStyle: { color: c.series[1], borderRadius: [3, 3, 0, 0] },
        }],
      };
    },

    // Claude dollars per merged ticket: {labels: [...], dollars: [...]}.
    "milestone-dollars"(data, c) {
      return {
        grid: { left: 48, right: 12, top: 16, bottom: 24 },
        tooltip: { trigger: "axis", valueFormatter: (v) => v == null ? "–" : dollars(v) },
        xAxis: {
          type: "category", data: data.labels,
          axisLine: { lineStyle: { color: c.rule } }, axisLabel: { color: c.ink },
        },
        yAxis: {
          type: "value", axisLabel: { color: c.muted, formatter: (v) => `$${v}` },
          splitLine: { lineStyle: { color: c.grid } },
        },
        series: [{
          name: "$/ticket", type: "bar", data: data.dollars, barMaxWidth: 36,
          itemStyle: { color: c.series[0], borderRadius: [3, 3, 0, 0] },
        }],
      };
    },

    // Net savings per milestone: {labels: [...], savings: [...]}.
    "milestone-savings"(data, c) {
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
          name: "Savings", type: "bar", data: data.savings, barMaxWidth: 36,
          itemStyle: { color: c.series[2], borderRadius: [3, 3, 0, 0] },
        }],
      };
    },

    // Ratings over time: {labels: [...], agents: [...], skills: [...], scores: [...]}.
    rating(data, c) {
      const agents = [...new Set(data.agents)];
      const series = [];
      for (const agent of agents) {
        const idx = agents.indexOf(agent);
        series.push({
          name: agent,
          type: "line",
          smooth: true,
          data: data.scores.map((s, i) => data.agents[i] === agent ? s : null),
          itemStyle: { color: c.series[idx % c.series.length] },
        });
      }
      return {
        grid: { left: 48, right: 12, top: 16, bottom: 24 },
        tooltip: {
          trigger: "axis",
          formatter: (p) => {
            if (p.length && p[0].data != null) {
              return p[0].seriesName + ": " + p[0].data;
            }
            return "";
          },
        },
        xAxis: {
          type: "category", data: data.labels,
          axisLine: { lineStyle: { color: c.rule } }, axisLabel: { color: c.ink },
        },
        yAxis: {
          type: "value", axisLabel: { color: c.muted },
          splitLine: { lineStyle: { color: c.grid } },
        },
        series: series,
      };
    },

    // Timeline: lanes per agent, bars per job, coloured by outcome.
    timeline(data, c) {
      const agents = data.lanes.map(l => l.agent);
      const bars = [];
      const markers = [];
      for (const lane of data.lanes) {
        for (const bar of lane.bars) {
          bars.push({
            value: [bar.start, bar.end, agents.indexOf(lane.agent)],
            itemStyle: { color: outcomeColor(bar.outcome) },
            ticket: bar.ticket,
            role: bar.role,
            minutes: bar.minutes,
            job_id: bar.job_id,
          });
        }
        for (const marker of lane.markers) {
          markers.push({
            value: [marker.at, agents.indexOf(lane.agent)],
            agent: marker.agent,
          });
        }
      }
      return {
        grid: { left: 60, right: 12, top: 16, bottom: 24 },
        tooltip: {
          trigger: 'item',
          formatter: (p) => {
            if (p.data && p.data.ticket) {
              return (p.data.ticket || 'N/A') + ' (' + p.data.role + ') &middot; ' + p.data.minutes + ' min';
            }
            return '';
          },
        },
        xAxis: { type: 'time' },
        yAxis: { type: 'category', data: agents },
        series: [
          {
            type: 'custom',
            renderItem: (params, api) => {
              const start = api.value(0);
              const end = api.value(1);
              const yPos = api.value(2);
              const height = api.size([0, 1])[1] * 0.6;
              const coord = api.coord([start, yPos]);
              const width = api.size([end - start, 0])[0];
              return {
                type: 'rect',
                shape: {
                  x: coord[0],
                  y: coord[1] - height / 2,
                  width: Math.max(width, 4),
                  height: height,
                },
                style: api.style(),
              };
            },
            data: bars,
          },
          {
            type: 'scatter',
            data: markers.map(m => [m.value[0], m.value[1], m.agent]),
            symbolSize: 10,
            itemStyle: { color: '#ff6b6b' },
            tooltip: {
              formatter: (p) => (p.data[2] || '') + ': refusal',
            },
          },
        ],
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
      // Timeline bars: clicking a bar opens the job page.
      if (el.dataset.chart === "timeline") {
        chart.on("click", (params) => {
          if (params.data && params.data.job_id != null) {
            window.location.href = "/jobs/" + params.data.job_id;
          }
        });
      }
      // Store the chart instance for theme redraws.
      el._chart = chart;
    }
  }

  // Redraw every chart with the new theme colours (f69-01).
  function redrawAll() {
    for (const el of document.querySelectorAll("[data-chart]")) {
      const chart = el._chart;
      if (!chart) continue;
      chart.dispose();
      delete el._chart;
      delete el.dataset.drawn;
    }
    draw(document);
  }

  document.addEventListener("DOMContentLoaded", () => {
    draw(document);
    // Partials htmx swaps in may hold charts too.
    document.body.addEventListener("htmx:afterSwap", (event) => draw(event.target));
    // Theme change: dispose and redraw every chart (f69-01).
    document.addEventListener("themechange", redrawAll);
  });
})();
