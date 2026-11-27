# Review: F291, the project picker's open list reads in the theme

**Status:** round 1 passed; the review tidied the milestone's tests itself. Ready for your sign-off.

### 1. What changed
- Open the Project picker in the top bar in the dark theme: the projects now read in the theme's light ink on its dark plate, not light grey on white.
- The closed picker looks the same as before, in both themes; the light theme's list now sits on its own plate too.

### 2. How to test it yourself
1. On your laptop, open the dashboard in the dark theme and click the Project picker: every project reads clearly on a dark plate.
2. Pick another project: the page reloads on it, as before.
3. Switch to the light theme with the top bar's switch and open the picker again: dark ink on the pale plate.
4. On your phone, open the picker: the phone draws its own list, so check it reads well there too.

### 3. Done when, as of now
- **Met:** in the dark and light themes, the options' computed background is `--plate` and their colour `--fg`, and the select's background is no longer transparent.
- **Met:** the closed picker keeps its size at 1440 px and 390 px (the test now compares it with the old transparent background).
- **Met:** choosing a project reloads the page with it (already covered by f256-01's test).
- **Met:** the tests pass and the colour test fails without the change; all gates passed.
- **Your check:** the phone's own picker list (iOS and Android draw it themselves and may ignore option colours).

### 5. Decisions made along the way
- **The developer's reload test was removed.** It only checked the form's method; f256-01's test already picks another project and checks the reload. *The review.*
- **The size test compares before and after.** The developer's compared 1440 px with 390 px, so it never measured "as before"; it now restores the old transparent background at each width and compares. *The review.*

### 6. What next
- **Factory:**
  > Simpler: tests/factory_dashboard/test_app.py repeats the same eight-line `route` function in 47 Playwright tests; one shared `serve(page, client)` fixture in its conftest would save about 350 lines.
  > The local model's tests for a Done when line sometimes check a stand-in (a form's method, two widths against each other) instead of the behaviour; make the developer's instructions say a Done when test must do what the line says, or name the existing test that does.

### 8. How the work went
- A one-line CSS cause found at planning made a one-attempt ticket; the gaps were in the tests: one duplicated an existing test, one measured the wrong comparison. The review fixed both in about 15 lines rather than spend another run.

<!-- runner report -->
<!-- runner report -->
