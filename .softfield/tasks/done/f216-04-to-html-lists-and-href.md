---
id: f216-04-to-html-lists-and-href
milestone: f216-let-s-redesign-the-milestone-review
difficulty: 4
depends_on: []
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
finding: f216-02-F1
---

### Goal
`_to_html` closes and nests its lists correctly and can't be made to break out of a link's `href`.

### Context
Read `_to_html` and `_inline_markup` in `factory_dashboard/milestones.py`, and the `test_to_html_*` tests in `tests/factory_dashboard/test_milestones.py` (f216-02's). Facts from the merged code:
- Two indented `- x` lines in a row: the second one is drawn in the outer `<ul>` after the nested one is closed, so it loses its indent.
- A nested `<ul>` is written beside its parent's `<li>`, not inside it.
- `1. a`, `- b`, `2. c` gives `<ol><li>a</li><ul><li>b</li><li>c</li>…`: the bullet opens a `<ul>` inside the open `<ol>` and the `2.` item then lands in that `<ul>`. `test_to_html_mixed_numbered_and_bullets` only counts tags, so it passes.
- `_inline_markup` puts the link's url in `href="…"` after escaping only `& < >`, so a `"` in the url ends the attribute (`[x](https://a"onmouseover="y)`).
- Bold and links are also applied inside `<code>`.
Tests should compare the whole output string for each case, not count tags.

### Done when
- two or more consecutive indented bullets under a bullet all sit in one nested `<ul>`, which is inside the parent's `<li>`
- a bullet between numbered items closes the `<ol>` or nests properly, and the output has balanced, well-formed tags (checked on the full string)
- a url containing `"` never produces an attribute other than `href`; it becomes plain text or is encoded
- text inside `` `code` `` isn't turned into bold or links
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 5918
gate_failures: ['stopped']
tokens: 3147262
```
