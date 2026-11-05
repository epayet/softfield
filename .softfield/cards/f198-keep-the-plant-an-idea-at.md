# Milestone F198: Plant an idea stays at the top, with Coming seeds under it

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-02.

## Notes
Keep the 'plant an idea' at the top rather than having 'coming seeds' before it so that when I want to plant something it's quickly available

## Today (read from the code, 2026-11-02)
`/planning` (`factory_dashboard/templates/planning.html`) shows the two tiles, then Coming seeds at full width when something is on its way, then a row of Plant an idea and Your desk. F63 chose this order (D1, "what you just did shows first"). So each plant pushes the box down, and the box goes back up when the runner takes the plant.

## Expected outcome
Plant an idea sits right under the two tiles, in the same place whether or not a plant is on its way. Coming seeds shows right under the box. Mock-up: [`f198-mockup/plant-first.html`](f198-mockup/plant-first.html).

## Decisions
- **D1 Plant first, replacing F63 D1.** The order is tiles, Plant an idea, Coming seeds, Your desk. F63's other decisions stand.
- **D2 Coming seeds joins the box's column.** On a wide screen it sits under the box, beside the desk, so neither the box nor the desk moves when it appears. On a phone it comes between the box and the desk, so a plant still shows at once, and the desk moves down while it's there. Under the whole row it would sit below a long desk on a phone, out of sight.
- **D3 The tiles stay above the box,** by the owner's rule that what's running comes first on a live page.

## Tickets
- `f198-01-plant-above-coming`: developer, D1 and D2. Small, unprotected, and the template's own code is its example.

## Done when
- Sending a plant leaves the box exactly where it was, on a phone and on a wide screen, and the plant shows right under it.
- With nothing on its way, there is no Coming seeds and the page looks as it does today.
- A note half typed in the box survives Coming's refresh.
