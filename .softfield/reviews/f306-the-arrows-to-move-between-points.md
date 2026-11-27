# Review: F306, on a phone the arrows to step through points stay put and headlines come first

**Status:** round 1 passed. The review fixed two bugs and the missing tests itself. Ready for your sign-off.

### 1. What changed
- On a phone, ◀ ▶ now sit above a reply's points and a review's key points, on a striped plate that says "Point 2 of 6". They stay in the same place whatever the point's length.
- Each point opens on its headline, now larger and in the dashboard's heading font. If you have scrolled down a long point, pressing ◀ or ▶ brings the arrows back to just under the top bar.
- On a computer, both pages look as before.
- Matches the mock-up. The sample F305 thread has no message with points, so its phone picture shows no arrows. On the review's phone picture, the floating "Your review" box covers the first headline, as it did before this card.

### 2. How to test it yourself
1. On your phone, open F306's conversation and unfold the lead's first reply: "Point 1 of 6" and ◀ ▶ sit under In short.
2. Press ▶ five times without scrolling: the arrows don't move, and each headline is right under them in large type.
3. On point 3, scroll down a little so the arrows go under the top bar, then press ◀: they come back just below the bar.
4. Do the same on F305's plan review.
5. On your computer, both pages look as before, with no arrows.

### 3. Done when, as of now
- **Met:** at 390 px, on a thread and a review, the count, dots and ◀ ▶ come before the first point, and stepping, commented dots and the 44 px controls work as before.
- **Met:** stepping through points with ▶, the arrows stay in place.
- **Met:** the nav reads "Point N of M" (the live review shows "Point 1 of 4").
- **Met:** with the nav under the top bar, ◀ or ▶ brings it back below the bar; with it in view, nothing scrolls. The review fixed this: it had stopped 60 px from the top, still under the phone's 100 px bar.
- **Met:** a point's title is 18 px on a phone on both pages. The review fixed threads, where an older rule had kept titles at 15 px. Wide screens are unchanged.
- **Your check:** steps 2 and 3 above, on the phone itself.

### 5. Decisions made along the way
- **The arrows come back on ◀ as well as ▶, to just below the measured top bar.** D3 asks for both. The developer did ▶ only and used a fixed 60 px, which is less than the phone's two-row bar. *The review.*

### 6. What next
- **Factory:**
  > When a ticket's Done when names a font size or a scroll, its test should check that exact value in the browser, because F306's developer left both untested and both were broken.
  > On a phone, tapping "Point 2 of 6" should open a short list of every headline, so I can jump straight to the one I want.

### 8. How the work went
- The local model built the layout and the plate as the mock-up drew them, in one attempt. It skipped the two Done when lines it couldn't check easily (the scroll-back and the 18 px title), and both were broken. Testing them was enough to find both bugs. The review fixed them in about 10 lines and added one test.

<!-- runner report -->
<!-- runner report -->
