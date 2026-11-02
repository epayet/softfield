# Milestone F68: I want the factory to be renamed SoftField. That should be…

> **State:** ready · **Priority:** 90 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
I want the factory to be renamed SoftField. That should be visible top left, let's talk through designs of a fun relevant logo too. also the top left text + logo should bring back to overview when clicked

## Outcome
- The dashboard is called SoftField: the top bar's left shows the logo and the name, and every page's title and the browser tab's icon say it.
- The logo and the name are one link back to the Overview, for the chosen project.
- The logo joins the field (the owner plants ideas) and the factory (crates, the hazard stripe), in the dashboard's own colours, so it follows the light and dark themes.

The picture: [`f68-mockup/logos.html`](f68-mockup/logos.html), four logos; A (the sprout in a crate) is the lead's pick until the owner chooses.

## Decisions
- **D1. Only what the owner sees is renamed.** The top bar, the page titles, the favicon and the FastAPI title. The metrics database (`~/.local/share/software-factory/`), the Dropbox backup folder, the bench cache and the `runner` commands keep their names: moving them risks the owner's data and backups for nothing seen. The extracted repo's name is ADR 02's question.
- **D2. The name is written SoftField,** "Soft" in yellow and "Field" in the sprout's green, logo A's two colours (the owner, 2026-10-09). The yellow is `--warn-ink`: the hazard yellow on the dark floor, the deeper amber on the light one (the hazard yellow there is 1.8:1, unreadable). The brand drops the all-capitals style, which would make it SOFTFIELD.
- **D3. The logo is inline SVG on the tokens** (`_partials/logo.svg`), so it follows the theme; the favicon is the same shapes with fixed colours.
- **D4. After F17.** f17-01 rebuilds the bar's phone row and f9-30 tests the brand's place in it; f68-01 waits for both.

## Not here
- A light or night switch: F69.
- Home-screen (PNG) icons for a phone: later, if the owner adds the dashboard to a home screen.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | softfield-brand | D | 3 | f17-01, f9-30 | logo and name top left, one link to the Overview; titles and favicon |
| 09 | logo-as-designed | L | 1 | – | the logo as the mock-up drew it: f68-01 redrew logo A (upright slats, thin curled leaves); the owner noticed, 2026-10-28 |
