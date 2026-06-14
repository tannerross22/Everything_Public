# Find in Note

In-editor text search, opened with **Ctrl+F**. Highlights every match in the currently open note and lets the user step through them with Enter / Shift+Enter.

Distinct from [[Search]] (Ctrl+P), which is vault-wide.

## UX

* **Ctrl+F** while in the editor → find bar appears at the top of the editor area, input focused.
* Type — all matches highlight with a yellow tint.
* **Enter** → jump to next match (also brighter highlight on the current one).
* **Shift+Enter** → previous match.
* **Escape** or × button → close (highlights cleared).

The match counter shows `N/M` where `N` is the current and `M` is the total.

## How it highlights

Uses the **CSS Custom Highlight API** — Chromium 105+. Two named highlights:

```ts
CSS.highlights.set('find-matches', new Highlight(...allRanges))   // all matches, subtle
CSS.highlights.set('find-current', new Highlight(currentRange))   // current match, bright
```

CSS:

```css
::highlight(find-matches) { background: rgba(249, 226, 175, 0.4); }
::highlight(find-current) { background: rgba(249, 226, 175, 0.8); color: #1e1e2e; }
```

Why this API and not `<mark>` tags? Because **wrapping text in DOM elements would corrupt ProseMirror's internal state.** Milkdown's view layer assumes the DOM matches its document model — inserting `<mark>` tags from outside would cause "node mismatch" errors next time the user types. The Highlight API renders the styling without touching DOM nodes.

## Match scanning

```ts
const textNodes = getTextNodes(proseMirror)   // TreeWalker over all text descendants
for (const textNode of textNodes) {
  const text = (textNode.textContent || '').toLowerCase()
  let startPos = 0
  while (startPos < text.length) {
    const idx = text.indexOf(term, startPos)
    if (idx === -1) break
    const range = document.createRange()
    range.setStart(textNode, idx)
    range.setEnd(textNode, idx + searchTerm.length)
    foundRanges.push(range)
    startPos = idx + 1
  }
}
```

Case-insensitive substring search per text node. Matches **don't span text nodes** — e.g. `<em>fo</em><em>o</em>` won't match query `foo` even though the visible text reads "foo." In practice this is fine because Milkdown rarely splits words across nodes.

## Navigation

```ts
const goToMatch = (index: number) => {
  if (matches.length === 0) return
  const wrapped = ((index % matches.length) + matches.length) % matches.length
  setCurrentIndex(wrapped)
  CSS.highlights.set('find-current', new Highlight(matches[wrapped]))
  matches[wrapped].startContainer.parentElement?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
```

* Wraps around (next of last → first, prev of first → last).
* Smooth scrolls to the current match.

## Lifecycle

* **Visible → true:** 50ms delayed focus (let the input mount first).
* **Visible → false:** clear `query`, `matches`, both highlights.
* **Open note changes:** [[App Component]] explicitly closes the find bar (`setFindVisible(false)`) on every `openNoteInTab` call, so the find state doesn't leak across notes.

## Where it lives

Rendered by [[FindBar Component]], positioned absolutely inside `.editor-area` in [[App Component]]:

```tsx
<div ref={editorContainerRef} className="editor-area">
  <FindBar visible={findVisible} onClose={() => setFindVisible(false)} containerEl={editorContainerRef.current} />
  <Editor … />
</div>
```

The `containerEl` ref is used by FindBar to query the `.ProseMirror` descendant for text nodes.

## What this doesn't do

* **No Replace.**
* **No regex.**
* **No "match case" / "whole word."**
* **No cross-tab search.**
* **No editor highlighting persistence** — closing the find bar clears the highlights immediately.

## Browser support

CSS Custom Highlight API is Chromium 105+. Electron ships modern Chromium, so this works in production. If running in an older Chromium, the highlights silently fail (the calls are wrapped in `try` blocks).

## Related

* [[FindBar Component]] — the implementation
* [[Search]] — vault-wide alternative
* [[App Component]] — `findVisible` state, Ctrl+F handler
* [[Keyboard Shortcuts]]
