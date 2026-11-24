---
id: f280-01-package-names-no-project
milestone: f280-a-lot-of-the-factory-assume
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/instructions/lead.md
  - runner/instructions/task-writing.md
  - runner/instructions/task-format.md
  - runner/instructions/bootstrap.md
  - runner/instructions/author/owner.md
  - runner/prompts.py
  - runner/gates.py
  - docs/workflow.md
  - .softfield/cards/f280-a-lot-of-the-factory-assume.md
tests:
  - tests/runner/test_prompts.py
---

### Goal
The factory's own instructions stop assuming every project is Coucou: no "Mum", no Coucou paths or French rules, and a test keeps them out.

### Context
Read "What happens today" and D1 to D5 in `.softfield/cards/f280-a-lot-of-the-factory-assume.md`; it lists every place, by file and section.
- Test first (D3): in `tests/runner/test_prompts.py`, one test that reads every `.md` under `runner/instructions/` (subfolders too), `runner/prompts.py`, `runner/gates.py` and `docs/workflow.md`, and fails on "coucou" or the whole word "Mum" in any case, listing each file and line. It must be red on main.
- `runner/instructions/lead.md`, "Sign-off sheet" items 1 and 6: say the people the project is for, as its `.softfield/project.md` names them, the owner when it names nobody (D2). "Review loop": the French line becomes "Check the project's user-facing language reads as its `.softfield/project.md` asks."
- `runner/instructions/bootstrap.md`, "The project's own rules": add who the project is for to what the file holds.
- `runner/instructions/task-writing.md`: remove the "JavaScript tasks (ADR 06)" section and the two French lines ("Lessons from M2" and "Open questions"); the rubric's i18n row says "translations" instead of "their French"; line 85's example path becomes a Softfield one (`runner/loop.py`). Keep the m-ticket anchors and lessons.
- `runner/instructions/task-format.md`: the example `files:` become neutral ("app/templates/compose.html"); the `.po` rule says "the project's translation files, when it has translations".
- `runner/prompts.py`: the three "coucou/x.py" examples become "app/x.py". `runner/gates.py`: the translations hint says "Add the missing translations to the project's .po catalogues and compile them with msgfmt." Leave `runner/i18n.py` as it is (D3).
- `docs/workflow.md` layout gate line: name `runner/` and `factory_dashboard/` only, or say "the project's source folders".
- `runner/instructions/author/owner.md`, "Factory theme", last bullet: "a project's own app keeps its own look".
- D4: paste every block you remove (task-writing's JavaScript section, the French lines, the review's French line, task-format's `.po` rule) word for word under "For Coucou" in the card doc, each under the name of the file it came from.

### Done when
- the new test fails on main, naming at least `runner/instructions/lead.md` and `runner/instructions/task-writing.md`, and passes after the change
- the sign-off sheet's items 1 and 6 in `runner/instructions/lead.md` name no person and point at `.softfield/project.md`
- every removed block is under "For Coucou" in `.softfield/cards/f280-a-lot-of-the-factory-assume.md`, word for word
- `tests/runner/test_prompts.py` passes as a whole (its tests read the real `runner/instructions/lead.md` headings: rename none)
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
