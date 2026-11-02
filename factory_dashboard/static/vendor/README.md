# Vendored files

Pinned copies for the factory dashboard, never edited by hand ([ADR 13](../../../.softfield/adr/13-factory-dashboard.md)). Protected: only the lead changes them.

| File | From | Version | sha256 |
|---|---|---|---|
| `htmx.min.js` | npm `htmx.org`, `dist/htmx.min.js` | 2.0.11 (npm integrity `sha512-Thx/Wtpe…636dtamA==`) | `d6fdc75f204e6bdefa99b69bf1e6d4ac69b8a364f77929f45c13476b4000f717` |
| `echarts.min.js` | npm `echarts`, `dist/echarts.min.js` | 6.1.0 (npm integrity `sha512-q0yaFPgg…pIyHZA==`) | `b66b25aeb4df84e33199dc21694014d336d222cbd9deb0e5a7c14bd6aa0d0fd0` |
| `fonts/chakra-petch-latin-500-normal.woff2` | npm `@fontsource/chakra-petch`, `files/` | 5.3.0 | `36ad966cb653de70ba37355c41003b02de8940b2df6cbcd46480a6ad8cadd65d` |
| `fonts/chakra-petch-latin-600-normal.woff2` | npm `@fontsource/chakra-petch`, `files/` | 5.3.0 | `a5888696e9eb1b4bbbecc8eb3922b8369f49d4bddb72263e033cbd17f399be76` |
| `fonts/chakra-petch-latin-700-normal.woff2` | npm `@fontsource/chakra-petch`, `files/` | 5.3.0 | `ce5095dc1cb200aaa939e38067a0677018d10e9f26ec38cdcf1557ac524fc775` |
| `fonts/barlow-latin-400-normal.woff2` | npm `@fontsource/barlow`, `files/` | 5.3.0 | `b0a8ad37ac45f5fb22ced461576db72e44e295107aad7a9c8a7a4bad728fd03b` |
| `fonts/barlow-latin-500-normal.woff2` | npm `@fontsource/barlow`, `files/` | 5.3.0 | `cd759df8ef9efc98fee14307b4eb5ba27f08b1f8f2f3ad2872432e25c89907a8` |
| `fonts/barlow-latin-600-normal.woff2` | npm `@fontsource/barlow`, `files/` | 5.3.0 | `4b52ddd4836b592df0e4832b8286956883cdc651b015126bdd18f184b7f90cc3` |
| `fonts/jetbrains-mono-latin-400-normal.woff2` | npm `@fontsource/jetbrains-mono`, `files/` | 5.3.0 | `14425ba9c695763c1547f48a206b7aa60350a33ae23de09f0407877f3fcd89eb` |
| `fonts/jetbrains-mono-latin-600-normal.woff2` | npm `@fontsource/jetbrains-mono`, `files/` | 5.3.0 | `400c6bfda18d5d14acad1c15d6dcb9f8e13c015e7286317e0b9a482539bef147` |

`htmx.LICENSE` is htmx's licence (Zero-Clause BSD). `echarts.LICENSE` (Apache 2.0) and `echarts.NOTICE` are ECharts'.

The fonts (f5-14) are Chakra Petch (display), Barlow (body) and JetBrains Mono (ids and numbers), the latin subset only (it covers French), all under the SIL Open Font License 1.1: `fonts/<family>.LICENSE` is each package's `LICENSE`. They were fetched once from jsDelivr's npm mirror (`https://cdn.jsdelivr.net/npm/@fontsource/<family>@5.3.0/files/<file>`); `dashboard.css` declares them with `@font-face`, so no page loads a font from elsewhere (AGENTS.md rule 7).

To update: fetch the tarball named by `npm view <package>@<version> dist.tarball`, check its sha512 against `dist.integrity`, copy the file above here, update this table, and run `tests/factory_dashboard` (`test_app.py` checks every `.js` and `.woff2` here against this table).
