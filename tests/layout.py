"""What a page looks like on a phone and a wide screen: overlapping or off-screen text and
controls (from Coucou's browser tests, for the dashboard's Playwright tests)."""

PHONE = {"width": 390, "height": 844}
DISPLAY = {"width": 1280, "height": 800}
_LAYOUT_JS = """() => {
  const SELECTOR = 'button, a, input, select, textarea, label, h1, h2, h3, p, li, img, '
    + '[role=button]';
  const name = (el) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')
    + (!el.id && el.className && typeof el.className === 'string'
       ? '.' + el.className.trim().split(/\\s+/).join('.') : '');
  const shown = [...document.querySelectorAll(SELECTOR)].filter((el) => {
    if (el.closest('[data-layout="overlay"]')) return false;
    // a closed <details> keeps a box for its hidden content in Chromium (f6-10)
    const closed = el.closest('details:not([open])');
    if (closed && !el.closest('summary')) return false;
    const style = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return style.visibility !== 'hidden' && style.opacity !== '0' && r.width > 0 && r.height > 0;
  });
  const problems = [];
  const width = document.documentElement.clientWidth;
  const scroll = document.documentElement.scrollWidth;
  if (scroll > width + 1) {
    problems.push(`the page scrolls sideways (${scroll}px > ${width}px)`);
  }
  // Inside a sideways scroller (the phone's tabs), off-screen is reached by scrolling
  const scrolls = (el) => {
    for (let p = el.parentElement; p; p = p.parentElement) {
      if (['auto', 'scroll'].includes(getComputedStyle(p).overflowX)) return true;
    }
    return false;
  };
  for (const el of shown) {
    const r = el.getBoundingClientRect();
    if ((r.left < -1 || r.right > width + 1) && !scrolls(el)) {
      problems.push(`${name(el)} leaves the screen sideways`);
    }
  }
  for (let i = 0; i < shown.length; i++) {
    for (let j = i + 1; j < shown.length; j++) {
      const a = shown[i], b = shown[j];
      if (a.contains(b) || b.contains(a)) continue;
      const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      const w = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
      const h = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
      if (w > 2 && h > 2) problems.push(`${name(a)} overlaps ${name(b)}`);
    }
  }
  return problems;
}"""


def layout_problems(page) -> list[str]:
    """Overlapping or off-screen text and controls on the page as it is now."""
    problems: list[str] = page.evaluate(_LAYOUT_JS)
    return problems
