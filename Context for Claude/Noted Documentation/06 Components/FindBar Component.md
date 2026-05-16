# FindBar Component

**Path:** `src/components/FindBar.tsx`

In-note text search, opened with **Ctrl+F**. Highlights matches inside the currently open note using the modern **CSS Custom Highlight API**.

This is different from [[SearchBar Component]] (Ctrl+P), which searches across the whole vault.

## Props

```ts
interface FindBarProps {
  visible: boolean
  onClose: () => void
  containerEl: HTMLElement | null    // typically the .editor-container ref
}
```

`containerEl` is the editor's outer `<div>`. The find logic queries the `.ProseMirror` descendant inside it.

## How highlighting works

```ts
const allHighlight = new Highlight(...foundRanges)
CSS.highlights.set('find-matches', allHighlight)

const currentHighlight = new Highlight(foundRanges[newIndex])
CSS.highlights.set('find-current', currentHighlight)
```

CSS Highlight API lets us style ranges of text **without mutating the DOM**. The corresponding CSS:

```css
::highlight(find-matches) {
  background: rgba(249, 226, 175, 0.4);
}
::highlight(find-current) {
  background: rgba(249, 226, 175, 0.8);
  color: #1e1e2e;
}
```

Two named highlights: `find-matches` for every match (subtle), `find-current` for the focused one (bright).

The advantage over the legacy `<mark>`-based approach: ProseMirror's document structure is untouched, so the user can still edit while the find bar is open without corrupting the editor's internal state.

## Search algorithm

```ts
const proseMirror = containerEl.querySelector('.ProseMirror') as HTMLElement
const textNodes = getTextNodes(proseMirror)   // walks descendants with TreeWalker
const term = searchTerm.toLowerCase()
const foundRanges: Range[] = []

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

* Case-insensitive substring search per text node.
* Re-runs on every query change.
* Doesn't span text nodes — a match split across ProseMirror node boundaries (e.g. inside formatting) would be missed.

## Navigation

* **Enter** — next match
* **Shift+Enter** — previous match
* **Escape** — close

`goToMatch(index)` wraps around `matches.length` (negative → last, > length → first), updates the `find-current` highlight, and `scrollIntoView`s the parent element of the current range.

## Lifecycle

* Visible→true: focus input with a 50ms delay (let the bar mount).
* Visible→false: clear `query`, `matches`, both highlights, and reset `currentIndex`.

The 50ms delay is because React batches the visibility flip with the input's mount in the same tick; focusing before paint is a no-op.

## Render

```tsx
<div className="find-bar">
  <input className="find-input" placeholder="Find…" value={query} … />
  <span className="find-count">{ matches.length > 0 ? `${currentIndex + 1}/${matches.length}` : '0 results' }</span>
  <button onClick={() => goToMatch(currentIndex - 1)}>▲</button>
  <button onClick={() => goToMatch(currentIndex + 1)}>▼</button>
  <button onClick={onClose}>×</button>
</div>
```

Positioned absolutely at the top of `.editor-area` in [[App Component]].

## What FindBar doesn't do

* No "Replace" mode.
* No regex.
* No "match case" / "whole word" toggles.
* Limited to the visible note — doesn't search across tabs.

## Related

* [[SearchBar Component]] — different feature (vault-wide)
* [[App Component]] — owns `findVisible` state and Ctrl+F handler
* [[Find in Note]] — feature view
