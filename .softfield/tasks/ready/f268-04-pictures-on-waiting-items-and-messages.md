---
id: f268-04-pictures-on-waiting-items-and-messages
milestone: f268-having-the-ability-to-upload-files
difficulty: 3
depends_on: [f268-01-pictures-stored-with-the-request, f268-03-add-a-picture-in-both-boxes]
area: factory
files:
  - factory_dashboard/thread.py
  - factory_dashboard/coming.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/planning.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_coming.py
---

### Goal
The owner's files show on their waiting plant in Planning's Coming panel and on their message on the thread: a picture as a thumbnail that opens full size, any other file as a chip that downloads.

### Context
The picture to build: `.softfield/cards/f268-mockup/pictures.html` (Proposed, the waiting message). A plant's or message's value carries `files`, a list of `owner_files` ids; each row has `name`, `mime` and `size`, and is served at `GET /files/{id}` (f268-01). `_messages` in `factory_dashboard/thread.py` builds a thread's messages from their request rows; `factory_dashboard/coming.py` builds the waiting plants. Reuse the `.thumb`, `.chip` and `.tray` styles f268-03 added to `factory_dashboard/static/dashboard.css`.

### Done when
- a waiting plant and an owner's message with files show one item per id, each a link to `/files/<id>`: a thumbnail when `mime` starts with `image/`, else a chip with the name and the size; a waiting one's items have the dashed orange edge, as the item does
- a message whose request is done still shows its files
- a plant or message without `files` renders exactly as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
