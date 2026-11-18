# ADR 49: Files with the owner's words

- **Status:** Accepted (by the owner, 2026-11-18)
- **Date:** 2026-11-18
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 18](18-dashboard-writes.md) item 2 ("the dashboard's only write is a request row"): a plant or a message may now carry files, written beside its row.
- **Evidence:** F268 (owner, 2026-11-18): "Having the ability to upload files in conversations would be helpful. For planting ideas too. Like a screenshot to show what I mean sometimes"; on the first plan: "Let's do other files. This is meant for the lead only usually" and "no changing of the original file". Today the Plant box and a thread's reply box take text only (`factory_dashboard/templates/planning.html`, `thread.html`), and `POST /requests` reads a url-encoded form (`factory_dashboard/requests.py`). The lead's planner jobs run on Claude, whose Read tool opens pictures, PDFs and text. The metrics database is copied to Dropbox every day and 14 copies are kept (`runner/backup.py`, `[backup] keep`).

## Decisions (⚑ = deviates from an earlier decision)
1. **Any file, as it is, up to 6 per plant or message and 25 MB each.** Screenshots, photos, PDFs, logs, anything. The page never changes a file: the bytes the lead gets are the bytes the owner picked. A file over 25 MB, or a seventh, is refused in the box at once, before anything is sent, with a line saying why.
2. ⚑ **The files travel with the words, in the same `POST /requests`.** The value's JSON gains `files`: each a name and a `data:` URL. The route checks the count and the size, then writes each to a new `owner_files` table (id, request id, name, type, size, bytes, path, created) in the same transaction as the request row, which keeps their ids instead. Still one route, one guard (ADR 18 item 3), and no file written by the dashboard.
3. **The database holds a file only until the runner's pick.** At its pick the runner writes the original to the project's `.softfield/var/files/<card or general>/<request id>-<n>-<name>` (not in git), copies it once to the backup folder's `files/<project>/` (Dropbox), records the path and empties the row's bytes. So a file has two copies, and the 14 daily database copies don't each carry it.
4. **They show at once, and only safely.** The waiting plant and the waiting message show each file with its dashed orange edge: a picture (PNG, JPEG, GIF or WebP, known by its first bytes) as a thumbnail that opens full size, any other file as a chip with its name and size that downloads. `GET /files/{id}` reads the bytes or the file read-only, sends `nosniff`, and shows inline only those four picture types; everything else, SVG and HTML included, goes as a download, so nothing a file holds runs in the dashboard.
5. **For the lead, not in git.** The files stay out of the repo, as the owner said they are for the lead. A plant's Notes get one line per file (name, size, its path under `.softfield/var/files/`). A planner job whose message carries files gets their paths in its prompt with "open each one with Read before you answer; say if one can't be opened". A ticket that needs one names its path in Context.

## Alternatives turned down
- **Shrinking pictures in the browser:** the owner wants the original file.
- **Files in git with the card:** a photo or a PDF of several MB stays in the history forever, for files only the lead reads.
- **Files kept in the database:** each of the 14 daily Dropbox copies would carry every file ever sent.
- **A second route, `POST /files`, uploading first:** a file sent but never followed by its words needs cleaning up, and the dashboard gains a second write.
- **Multipart upload (`UploadFile`):** needs `python-multipart`; base64 inside the value costs a third more bytes on the home Wi-Fi only.

## Consequences
- `.softfield/var/files/` and the backup folder grow by what the owner sends; nothing removes a file (an archived card keeps its files).
- A file the lead can't open (a zip, a Word file, an iPhone HEIC photo) reaches it as a path it says it couldn't read.
- Anyone on the home Wi-Fi can send a file, as they can send words today (ADR 18 item 3).

## What doesn't change
- The guard on `POST /requests`, git's one writer, the plant and message flow, and what a message or a plant may say.
