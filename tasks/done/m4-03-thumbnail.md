---
id: m4-03-thumbnail
milestone: 4
depends_on: []
files:
  - coucou/static/coucou/js/thumbnail.js
tests:
  - tests/browser/test_thumbnail.py
---

### Goal
`thumbnail(file, {max = 320}) → Promise<string>`: a small JPEG data URL of a photo, for the delivery list.

### Context
A plain module, no Preact and no strings (nothing to translate). Follow the shape of `coucou/static/coucou/js/render.js` and the harness use in `tests/browser/test_render.py`. Decision D6 in `docs/milestones/m4.md`.
- The longest side becomes `max` pixels (a smaller photo isn't enlarged); the ratio is kept.
- **Orientation is kept**: decode with `createImageBitmap(file, {imageOrientation: "from-image"})`, so an EXIF-rotated phone photo comes out upright. Draw on a canvas, return `toDataURL("image/jpeg", 0.7)`.
- A file that can't be decoded rejects (the caller decides what to show).
- Tests build plain images in the page with a canvas (`toBlob`). For the rotation case, make the JPEG in the test with Pillow (already a dependency): a landscape image saved with EXIF orientation 6 (`exif = Image.Exif(); exif[0x0112] = 6`), handed to the page through `page.route` or as bytes. You can't write binary files, so don't add an image file.

### Done when
- a 1000×500 image gives a data URL that decodes to 320×160; a 200×100 image stays 200×100
- `{max: 100}` is honoured
- the result starts with `data:image/jpeg`
- an EXIF-rotated portrait fixture comes out portrait (height > width)
- a non-image file rejects
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 3023
gate_failures: ['mypy']
tokens: 3547962
```
