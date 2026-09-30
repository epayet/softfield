# Preact + htm in Coucou

One page, for the version we vendor ([ADR 11](../adr/11-preact-ui.md)): `coucou/static/coucou/vendor/preact-htm.js`, htm 3.1.1 with its bundled Preact 10. No web docs: they describe newer versions. **Worked example:** `coucou/static/coucou/js/name_form.js` and `tests/browser/test_name_form.py`. Copy their shape.

## Importing
```js
import { html, useState, useEffect, useRef } from "../vendor/preact-htm.js";
```
- Always this relative path. No build step, no import map, no npm package.
- Everything the file exports: `html`, `render`, `h`, `Component`, `createContext`, `useState`, `useReducer`, `useEffect`, `useLayoutEffect`, `useRef`, `useImperativeHandle`, `useMemo`, `useCallback`, `useContext`, `useDebugValue`, `useErrorBoundary`. Nothing else: no `Fragment`, no `useId`, no signals.

## A component
```js
export function Counter({ start, onDone }) {
  const [count, setCount] = useState(start);
  return html`
    <p>${interpolate(gettext("%s taps"), [count])}</p>
    <button type="button" onClick=${() => setCount(count + 1)}>${gettext("Tap")}</button>
    <button type="button" onClick=${() => onDone(count)}>${gettext("Done")}</button>
  `;
}
```
- **One concept per module**, a named `export function`. Props in, callbacks out (`onSave`, `onSend`…). The component never calls `fetch` or `api()`: whoever mounts it passes a callback that does (see `me.js`).
- **Several roots** are fine: htm returns them as a list.
- **A component inside a template:** `<${NameForm} name=${name} onSave=${save} />`. Pass all props at once with `<${Compose} ...${props} />`.
- **If/else:** `${busy ? html`<p>…</p>` : null}`. `null` shows nothing.
- **Lists:** `${items.map((item) => html`<li key=${item.id}>${item.note}</li>`)}`. Always give a `key`.

## Attributes and events
- Values go in `${}`: `value=${text}`, `disabled=${busy}` (`false` removes the attribute), `hidden=${!open}`.
- `class`, `for`, `maxlength`, `aria-*` and `id` are written as in HTML.
- **Text inputs use `onInput`**, not React's `onChange`, which only fires when the field loses focus: `onInput=${(e) => setText(e.currentTarget.value)}`.
- Forms: `onSubmit=${submit}`, and `event.preventDefault()` first thing in `submit`.
- Files: `<input type="file" accept="image/*" onChange=${pick} />`. For a file input, `onChange` is right.

## Hooks
- `useState(initial)` returns `[value, setValue]`. Never change a state array or object in place: `setItems([...items, item])`.
- `useEffect(() => { …; return () => cleanup(); }, [deps])` is for timers, listeners and object URLs. Clean up what you start (`URL.revokeObjectURL`, `clearInterval`).
- `useRef()` holds a DOM element (`ref=${input}`, then `input.current.focus()`) or a value that shouldn't re-render.
- Call hooks at the top of the component, never inside `if`, loops or callbacks.

## Text: `gettext()`
- `gettext` and `interpolate` are globals. The page loads `/jsi18n/` before the modules.
- Write every sentence as one literal: `gettext("Please write a name.")`. Never build it from pieces or a variable, because the extractor only reads literals.
- Numbers and names go through `interpolate`: `interpolate(gettext("%s / 280"), [text.length])`, or named: `interpolate(gettext("Sent to %(space)s"), { space: name }, true)`.
- Add each new string to `coucou/locale/fr/LC_MESSAGES/djangojs.po` with its French, then compile it: `msgfmt -o coucou/locale/fr/LC_MESSAGES/djangojs.mo coucou/locale/fr/LC_MESSAGES/djangojs.po`.

## The page's rules (CSP)
Scripts only from our own files: no inline `<script>`, no `eval`, no CDN. Style with classes in the page's CSS, not `style=` strings. Images may be `blob:` or `data:` URLs (previews, thumbnails).

## Tests (`tests/browser/test_<module>.py`)
- `mount(harness, "name_form", "NameForm", "{name: 'Mum', onSave: async (n) => { window.saved.push(n); return true; }}")` from `tests/browser/conftest.py` renders the component on the harness page. Props are a JavaScript expression, and callbacks record what they got on `window`.
- The harness serves the real `/jsi18n/`, in English, so tests read English text.
- Find things as a person would: `page.get_by_role("button", name="That's me")`, `page.get_by_label(…)`, `page.get_by_role("alert")`.
- **`page.evaluate` needs a function to set things:** `page.evaluate("() => { window.answer = false; }")`. A bare `"window.answer = …"` returns the value, and if that's a Promise, Playwright waits for it forever.
- Wait for results with `locator.wait_for()` or `page.wait_for_function("() => window.saved.length === 1")`, never `sleep`. **Always pass `wait_for_function` a function (`"() => …"`)**: a bare expression is `eval`'d while it polls, and the real pages' CSP blocks that (`EvalError: … 'unsafe-eval'`). It hides on the harness page and fails on `/me/` (m4-06).
- `localStorage` starts empty in every test. Reload with `mount` again to check that something is remembered.
- End with `layout_problems(page) == []` at `PHONE`.
