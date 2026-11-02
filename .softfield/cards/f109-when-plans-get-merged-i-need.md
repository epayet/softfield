# Milestone F109: Merged cards link to each other, both ways

> **State:** done · **Priority:** 1 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-15. Base: git tag `f109-when-plans-get-merged-i-need-start`. Report: [`.softfield/reviews/f109-when-plans-get-merged-i-need.md`](../reviews/f109-when-plans-get-merged-i-need.md).
> Planted by the owner on 2026-10-13.

## Notes
When plans get merged, I need to be able to go from one to the other (I have no links ATM)

## Expected outcome
A card that was merged away and the card that took its notes link to each other on their thread pages, both ways, for every merge already done too. A card's key is never given to a new card after a merge, so one thread is one conversation.

## Done when
- On the thread of a card merged away (`/planning/f105`), the header says "Merged into F51, <its title>" and that is a link to F51's thread. The header shows the merged card's own title, not its bare key.
- On the kept card's thread (`/planning/f51`), the header lists "Merged here" with one link per merged card (F16, F105), each with its title and the date.
- The lead's line "The conversation goes on on F51's thread: /planning/f51" shows its path as a link.
- After the highest card is merged away, the next plant takes a new key, not that card's.
- To test: open `/planning/f107` and `/planning/f95` on the phone and go from one to the other and back; then plant two notes that say the same thing, let the lead merge them, plant a third, and check it got a new number.

## Decisions
- **D1 The links live in the thread page's header,** under the card's title: where the owner lands from the desk, above the fold on a phone, and each link is a 44px row. Not a new page, and not the desk.
- **D2 The links are read from the cards on main, not stored.** Every merge writes a heading in the kept card's Notes, `### From F107: <title> (merged by the lead on 2026-10-13)` (`planner.merged_card`, through `_merge`). The dashboard reads those headings from `.softfield/cards/` in the project's checkout: no new column, nothing in `runner/`, and the 19 merges done before this card get their links too. A test builds its doc with `planner.merged_card`, so the writer and the reader can't drift apart. With no checkout (a project whose repo is a URL), no links show.
- **D3 A chain shows its end.** When the kept card is merged on, its Notes move with their headings one level down (`card_notes`), so the reader takes headings of three to six `#` and the first card's thread links straight to the card that holds its notes now.
- **D4 A key used twice shows every merge.** Until f109-02, a merged card's key went to the next plant when it was the highest (`next_key` counts docs and tickets only): F64 was planted and merged three times (into F13, F42 and F9), F73 and F107 twice, and each key's thread holds all those conversations. Such a thread lists every card it was merged into, with its date. When the key has a card again (F73 today), the line reads "An earlier F73 was merged into F43, <title>".
- **D5 A key with a thread is never planted again** (f109-02): `_plant` gives `next_key` the keys the planning threads use too (`metrics.thread_cards`), so the next key is one past the highest of docs, tickets and threads. The threads already mixed stay as they are (D4 names them); splitting them isn't worth a migration.
- **D6 Paths in the lead's plain lines are links:** a lead message without points shows `/planning/<key>` as a link (escaped first, then linked; the owner's own messages stay plain text). F49's line on the kept thread ("Merged F44 here: …", f49-02) is left as it is: the header already links back.
- **D7 A merged-away card's page points on** (the owner, 2026-10-13, after writing "Go" on F107's page): in place of the box to write in, "Merged into F95, <title>: the conversation and its plans are there", with the kept card's open proposals as links. Since f49-03 the runner sends a message written there to the kept card's thread anyway (`_plan_message`), so no words are lost meanwhile. A kept card already planned says so, with its tickets' count, linking to its card. With two kept cards (a number used twice before f109-02: F64, F73, F107) the page shows one such block per kept card and keeps its box to write in, since the runner can't tell which card a message is for. The owner (2026-10-13): seeing the related plan from any merged card "is the main thing that was confusing me".

## Tickets
| # | Ticket | Agent | Difficulty | Depends on | What |
|---|---|---|---|---|---|
| 01 | merge-links | developer | 4 | f22-01 | D1 to D4, D6: the header's links both ways, the merged card's title, the path as a link |
| 02 | keys-not-reused | lead | 3 | | D5: a plant never takes a key a thread has. Done by the lead with the owner, 2026-10-13 (`eda0843`) |
| 03 | merged-page-points-on | developer | 4 | 01 | D7: the merged card's page says where to go, in place of the message box |

## Later
- The same links on the card's page (F5's f5-17-card-page builds it): once that page is on main.
