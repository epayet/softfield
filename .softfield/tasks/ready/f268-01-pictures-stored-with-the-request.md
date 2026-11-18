---
id: f268-01-pictures-stored-with-the-request
milestone: f268-having-the-ability-to-upload-files
agent: lead
difficulty: 5
depends_on: []
area: factory
files:
  - runner/metrics.py
  - factory_dashboard/requests.py
tests:
  - tests/factory_dashboard/test_requests.py
  - tests/runner/test_metrics.py
---

### Goal
A `plant` or `plan_message` sent with files stores them, byte for byte, in a new `owner_files` table beside its request row, and the dashboard serves each one back safely.

### Context
Read ADR 49 (`.softfield/adr/49-pictures-with-the-owners-words.md`) items 1, 2 and 4, and D1–D3 in `.softfield/cards/f268-having-the-ability-to-upload-files.md`. The table is a new migration step in `runner/metrics.py` (the `PRAGMA user_version` loop), next to `owner_requests`. `POST /requests` in `factory_dashboard/requests.py` keeps its guard and its one write connection (`writable`); the files go in the same transaction as the request row. Both `runner/` and this route are protected (security): tests first.

### Done when
- a `plant` and a `plan_message` whose value carries a PNG, a PDF and a text file write one request row whose value's `files` is the three new ids, and three `owner_files` rows with that request's id, the cleaned name (D2), the size, the type from the first bytes (`image/png`, else `application/octet-stream`), the exact bytes sent, and no path
- a file over 25 MB, a seventh file, a `files` that isn't a list of name and `data:` URL, or `files` on any other kind is a 400 with the reason, and nothing is written, the request row included
- `GET /files/{id}` answers the bytes with `X-Content-Type-Options: nosniff`; PNG, JPEG, GIF and WebP inline with their type; anything else, an SVG or an HTML file labelled `image/png` included, as `application/octet-stream` with `Content-Disposition: attachment` and the cleaned name
- once a row's bytes are emptied and its `path` set, `GET /files/{id}` serves the file at `path`, only when it lies under the project's `.softfield/var/files/`; an unknown id or a missing file is 404
- a value without `files` is stored exactly as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
