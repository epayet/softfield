# Vendored files

Pinned copies for the factory dashboard, never edited by hand ([ADR 13](../../../docs/adr/13-factory-dashboard.md)). Protected: only the lead changes them.

| File | From | Version | sha256 |
|---|---|---|---|
| `htmx.min.js` | npm `htmx.org`, `dist/htmx.min.js` | 2.0.11 (npm integrity `sha512-Thx/Wtpe…636dtamA==`) | `d6fdc75f204e6bdefa99b69bf1e6d4ac69b8a364f77929f45c13476b4000f717` |
| `echarts.min.js` | npm `echarts`, `dist/echarts.min.js` | 6.1.0 (npm integrity `sha512-q0yaFPgg…pIyHZA==`) | `b66b25aeb4df84e33199dc21694014d336d222cbd9deb0e5a7c14bd6aa0d0fd0` |

`htmx.LICENSE` is htmx's licence (Zero-Clause BSD). `echarts.LICENSE` (Apache 2.0) and `echarts.NOTICE` are ECharts'.

To update: fetch the tarball named by `npm view <package>@<version> dist.tarball`, check its sha512 against `dist.integrity`, copy the file above here, update this table, and run `tests/factory_dashboard`.
