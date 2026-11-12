# Milestone F199: The factory floor: a small strip on the Overview and a one-screen map

> **State:** ready · **Priority:** 4 · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-02.

## Notes
Let's improve the factory floor it's not very good ATM and a bit too big on mobile especially. Planted rows is not super helpful. Remember arknight Endfield for inspiration. Eventually I'll want an android widget to be able to see quickly what's going on ATM, and an embedded version of the factory to include in my website. I wonder if a small version and a full screen version where you can see all the components from a glance a bit like a map be cool, open to ideas

## Outcome
- The Overview shows the floor as a **strip**: one belt, six stops, one line saying what runs, about 170 px tall on any screen. It sits under Now and the Queue.
- **The map** is its own page, `/floor`: the whole factory from above on a grid, every machine, belt and pile on one screen with no scrolling, upright on a phone, sideways or wide on anything else, with a Full screen button.
- Planted rows are gone. Every planted card is one tile, in the board's order.
- Tapping anything on the map says what it is.

The picture to build: `.softfield/cards/f199-mockup/floor.html`.

## Why
- **Too big:** the phone floor is 358 × 1740 units (`PHONE_HEIGHT`), about 1,900 px on a 390 px phone, 2 to 3 screens. The wide one needs 1,100 px or it scrolls sideways.
- **Planted rows say little:** they show the first four cards by number, not by the board's order. On 2 Nov they were Bugs, F9, F10 and F25, of 57 planted, while the line was on F170, F187 and F85. They take 262 of the phone's 1740 units.
- **Words on belts collide:** 13 belts carry labels up to 40 characters, which is why f3-27 exists.
- **Every new shape is drawn by hand:** two sets of absolute coordinates today (`BELTS`, `PHONE_BELTS`, `AREAS`, `PHONE_AREAS`). Adding sizes that way would make four.

## Decisions
- **D1. One document, two sizes.** Both are drawn from `live_line`'s document. The strip is the small one, the map the full one. Crates, waits, the checks light, the 5-second refresh and F132's project plates keep their meaning.
- **D2. The map's page** (f199-01): `GET /floor`, in `factory_dashboard/line.py`, template `factory_dashboard/templates/floor.html` extending `base.html`, with the top bar and tabs hidden for a thin bar of its own. One `svg#map`, sized to the screen with no scrolling. `/line` keeps redirecting to `/`, and `/line/live` keeps serving the document.
- **D3. Geometry lives in two tables** (f199-01): `WIDE` (960 × 540) and `TALL` (360 × 640) in `factory_dashboard/static/factory.js`, as in the mock-up's script, drawn by one function. A shape picks its table: as wide as tall or wider, `WIDE`. Everything sits on a 20-unit grid. A coordinate outside those tables is a bug.
- **D4. The tiles** (f199-01): `doc.field.planted`, live only, from `board()`'s planted stage in its order: `{key, title, done, total, growing, bug}`. A replay has no board, so it draws `field.rows` as tiles in their own order.
- **D5. Words:** the map uses the board's stage names (Seed, Sprouting, Planted, Ripe, Harvested). Belts carry no words, only today's number when above zero; the words go to a tap (f199-04).
- **D6. The strip is plain HTML** (f199-02), `factory_dashboard/templates/_partials/strip.html`, from `glance(doc)` in `factory_dashboard/line.py`: `{status: {words, kind}, planted, queue, machines: [{name, station, state}], merged, ripe}`. Counts, machine states and a short status line only, no titles, so a later widget or website can use it as it is. It refreshes with `/live`, as `#now` does.
- **D7. Replay moves to the map** (f199-03). The Overview's While you were away keeps its own choice of stretch, which today lives in the replay bar.
- **D8. Not in this card:** crates travelling along belts (F10, Crates on the belts, draws on the new map), the Android widget and the website version (two seeds of their own).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | the-map | L | 8 | f132-05 | `/floor`, the two tables, tiles, machines; also takes f9-27 off the queue |
| 02 | strip | D | 5 | 01 | `glance`, the strip on the Overview, under Now |
| 03 | replay-on-the-map | L | 6 | 01, 02 | replay on the map, the old drawings and their tests gone |
| 04 | map-taps | D | 3 | 01 | a tap on any station, machine or belt says what it is |
| 05 | full-screen-and-key | D | 3 | 01 | the Full screen button, and the key behind "?" on a phone |
