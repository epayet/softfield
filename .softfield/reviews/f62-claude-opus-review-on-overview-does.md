# Review: F62, a review on Now says which card it reviews

- **Status:** reviewed (round 1). Two developer tickets (f62-02, f62-03) are queued for the places still missing; sign-off comes after them.

## Sign-off sheet

### 1. What changed
- On the Overview's Now panel, a review, a planner reply or a checkpoint now shows its card's key on a small plate linking to the card's page, the card's title and one line on what the job does ("The lead reads what F62 built, before it's yours to sign off").
- A developer job with a ticket looks as before, and so does a job with no card.

### 2. How to test it yourself
1. While a review or a planner reply runs (one runs at every reply in the Planning room), open the Overview on your phone.
2. Under Now, check the plate next to "attempt 1" shows the card's key (e.g. F62), with the card's title and the one-line "what it does" below.
3. Tap the plate: it opens that card's planning page.

### 3. Done when, as of now
- **Met:** while a review runs, Now shows the card's key linked to its page, its title and "The lead reads what F… built, before it's yours to sign off". The live page showed this for this review.
- **Not yet:** the top bar still reads "Running: softfield · review, job 2591"; f62-02 makes it "review F62".
- **Not yet:** Next in line still says "a batch" for a due review; f62-02.
- **Met:** a planner reply and a checkpoint name their card the same way on Now, and a job with neither ticket nor card shows as before. **Not yet:** the Projects page, the Planning room and the Jobs list; f62-03.
- **Your check:** on a phone, while a review or a planner reply runs.

### 5. Decisions made along the way
- **The first ticket covered Now only.** It's the place the owner looks first, and the rest was meant for a later ticket, but none was written; the review added f62-02 and f62-03. *The lead, f62-01.*
- **The card's plate, not a plain link.** The developer drew the calmer variant; the review switched to D3's plate (F132's project plate, as a link) and made the role line quieter, as the mock-up's Proposed shows. *The review.*
- **The card's title comes from the database's card title,** which the runner keeps in step with the card's heading, instead of reading the card's file. *The lead, f62-01.*

### 6. What next
- **Factory:** when the lead narrows a ticket to part of a card's Done when, it should write the tickets for the rest straight away, so nothing waits for a review to notice.
  > When a ticket leaves part of its card's Done when "for a later ticket", the planner writes that later ticket in the same plan, and check-tickets warns when a card's Done when names a place no ticket lists.

### 8. How the work went
- The local model stopped twice after 20 minutes with no edit, then passed on its third try after the lead's direction (about 2 h in all). The work was small; the stall was in getting started.
- The developer edited an existing test by deleting its assertion instead of updating it; the review restored a real check.

### 9. What clogged the factory line
- 42 min on two local attempts that stopped with no edit (jobs 2586, 2587) before the lead's direction; the direction should come at the first stall, not the second.

<!-- runner report -->
<!-- /runner report -->
