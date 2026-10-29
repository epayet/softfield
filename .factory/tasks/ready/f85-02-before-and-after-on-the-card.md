---
id: f85-02-before-and-after-on-the-card
milestone: f85-when-i-sign-off-a-task
agent: lead
difficulty: 4
depends_on: [f85-01-pictures-at-the-review]
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
A ripe or signed-off card with pictures, in any project, shows a "Before and after" panel right under "What changed" on its page, with a Before / After switch and a Phone / Wide switch, each picture tappable to full size.

### Context
The picture to build: `.factory/cards/f85-mockup/before-after.html` (Proposed). Read D5 to D7 in `.factory/cards/f85-when-i-sign-off-a-task.md`, then `milestone_page` (`/milestones/{key}`) in `factory_dashboard/milestones.py`, `factory_dashboard/templates/milestone.html` and the `.about` plate in `factory_dashboard/static/dashboard.css` (the panel's header, stripe and corner ticks follow it). The card's list file (D4: the addresses, and per picture taken or why not) and the pictures are written by f85-01's script.
- The panel shows only when the card's list file exists in its folder under the card's project's `.factory/var/shots/` (the page's `?project=` picks the project, as the rest of the page does), and only where "What changed" shows.
- `/milestones/{key}/shots/{file}` (with `?project=`) serves a picture from that project's card folder only when `file` matches D5's names (`(before|after)-(phone|wide)-<n>.png`); any other name, a path with `/` or `..`, or a missing file is 404. It serves `image/png` and nothing else. The owner's page never needs anything else from that folder.
- Each plate's address is a link to the page as it is now, opening in a new tab (`target="_blank" rel="noopener"`): on Softfield, the dashboard address with the page's `?project=`; in another project, the address joined to its `[shots] live` (read with f85-01's settings). With no `live`, the address is plain text. Only an address from the card's list becomes a link, and only to `live` or the dashboard itself.
- A picture not taken shows its reason as D6 words it, in a dashed plate the size of the picture, never an empty frame.
- The switches change only what is shown, on the page itself (no request). Before is shown first on a phone; on a wide screen Before and After sit side by side and the Before / After switch is hidden. Phone is chosen first on a narrow screen, Wide on a wide one.
- "The plan's mock-up ›" links to the card's mock-up proposal on its planning thread when it has one; leave it out otherwise.
- New colours or shapes join the tokens at the top of `dashboard.css` first; the ornament (ticks, stripe) uses the ink and the hazard stripe only.

### Done when
- a card with a list file shows the panel under "What changed", with one plate per address in the list's order
- a card without it shows no panel, as today
- `/milestones/<key>/shots/after-phone-1.png` serves the file; `../`, another extension, another card's name and a missing file are 404; a travel-companion card's pictures come from travel-companion's folder, not Softfield's
- a before recorded as didn't exist before shows "This page didn't exist before" in place of the picture
- a Softfield card's `/board` plate links to `/board?project=softfield` in a new tab; a project with `live` links to its app; one without shows plain text
- in Chromium at 390 px, the Before / After switch flips the pictures; at 1440 px both show side by side
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
