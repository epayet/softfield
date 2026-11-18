# Milestone F268: Add pictures to a plant or a thread message

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
Having the ability to upload files in conversations would be helpful. For planting ideas too. Like a screenshot to show what I mean sometimes

(2026-11-18, on the thread) Let's do other files. This is meant for the lead only usually. No changing of the original file.

## Expected outcome
The owner adds any file (a screenshot, a photo, a PDF, a log) to a plant or a thread message, from the phone or the desk, sees it at once on the waiting item, and the lead's reply shows it opened it. The file reaches the lead exactly as it was picked.

## Done when
- The Plant box and a thread's reply box each have "Add a file": the phone's photos, camera or files, a paste or a drop on a wide screen; up to 6 of 25 MB each, shown before sending (a picture as a thumbnail, any other file as a chip with its name and size), each with a remove ✕.
- The waiting plant and the waiting message show their files with the dashed orange edge; a picture opens full size, any other file downloads.
- After the runner's pick, each file is in `.softfield/var/files/` and the backup folder, byte for byte, and a planted card's Notes list it.
- A planner job on a message with files names each one in its reply, or says it couldn't open it.

## Decisions
The rules are [ADR 49](../adr/49-pictures-with-the-owners-words.md); the joints:
- **D1, the value:** a `plant` or `plan_message` value's JSON gains `files`, a list. From the page each is `{"name": "<the file's name>", "data": "data:<type>;base64,…"}`; once `POST /requests` has stored them, the row's value holds their `owner_files` ids instead (`"files": [12, 13]`). `runner/requests.py` and `runner/planner.py` only ever see ids.
- **D2, the table:** `owner_files(id INTEGER PRIMARY KEY, request_id INTEGER, name TEXT, mime TEXT, size INTEGER, bytes BLOB, path TEXT, created TEXT)`, a new migration step in `runner/metrics.py`. `name` is the file's name cut to its last part and to `[A-Za-z0-9._-]`, other characters as `-`, at most 80 long, `file` when empty. `mime` is `image/png`, `image/jpeg`, `image/gif` or `image/webp` from the first bytes, else `application/octet-stream`; the data URL's label is never trusted. At most 6 per request and 25 MB each, else 400 with the reason, before anything is written.
- **D3, serving:** `GET /files/{id}` in `factory_dashboard/requests.py`, read-only: the row's bytes, or once they're emptied the file at `path` (under the project's `.softfield/var/files/` only). `X-Content-Type-Options: nosniff` always; the four picture types inline, everything else `application/octet-stream` with `Content-Disposition: attachment; filename="<name>"`. 404 for an unknown id or a missing file.
- **D4, the box:** one script, `factory_dashboard/static/files.js`, used by both boxes: picker (`multiple`, no `accept`), paste, drop, previews with ✕, the refusals (a seventh, over 25 MB) shown in the box, and a `files(form)` function the `hx-vals` call to add `files`. It reads each file with `FileReader.readAsDataURL` and never re-encodes it.
- **D5, the pick:** applying a plant or a message, the runner writes each file to `.softfield/var/files/<card or general>/<request id>-<n>-<name>`, copies it to `<backup dir>/files/<project>/` under the same name (skipped, and said in the run log, when no backup folder is set), sets `path` and empties `bytes`. A plant's Notes get, under the words, `Files (for the lead, not in git):` and one bullet per file: name, size, path.
- **D6, the lead:** `runner/planner.py`'s `prompt` adds, after the owner's words, "The owner attached N files: <path (type, size)>… Open each one with Read before you answer; say in a point if one can't be opened." `PLANNER` in `runner/prompts.py` gets one line saying a file is part of the note.

## Before and after
- `/planning`
- `/planning/f268`

The mock-up: [`f268-mockup/pictures.html`](f268-mockup/pictures.html).
