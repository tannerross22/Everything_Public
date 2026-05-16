# SearchBar Component

**Path:** `src/components/SearchBar.tsx`

The full-vault search overlay opened with **Ctrl+P**. Searches note **names first** (instant), then **content** (debounced) with a 30-char snippet around each match.

## Props

```ts
interface SearchBarProps {
  notes: NoteFile[]
  onOpenNote: (path: string) => void
  visible: boolean
  onClose: () => void
}
```

`notes` is the flat list from [[useVault]] (originally from [[listNotes]]).

## Behavior

### Open / focus
On `visible: true`, autofocus the input and reset state:

```ts
useEffect(() => {
  if (visible) {
    inputRef.current?.focus()
    setQuery('')
    setResults(notes.map(n => ({ note: n })))
    setSelectedIndex(0)
  }
}, [visible, notes])
```

Empty query shows all notes — useful as a "command palette" for opening any note by name.

### Name search (synchronous)

```ts
const nameMatches = notes
  .filter(n => n.name.toLowerCase().includes(q))
  .map(n => ({ note: n }))
setResults(nameMatches)
```

Updates on every keystroke. Pure in-memory filter — fast for ~thousands of notes.

### Content search (debounced 250ms)

After 250ms of typing inactivity, kicks off a content scan:

```ts
debounceRef.current = setTimeout(() => searchContent(q, nameMatches), 250)

const searchContent = async (q, nameMatches) => {
  const contentMatches: SearchResult[] = []
  for (const note of notes) {
    if (nameMatches.some(m => m.note.path === note.path)) continue
    const content = await window.api.readNote(note.path)
    const idx = content.toLowerCase().indexOf(q)
    if (idx !== -1) {
      const start = Math.max(0, idx - 30)
      const end = Math.min(content.length, idx + q.length + 30)
      const snippet = (start > 0 ? '...' : '') + content.slice(start, end) + (end < content.length ? '...' : '')
      contentMatches.push({ note, snippet })
    }
  }
  setResults([...nameMatches, ...contentMatches])
}
```

Snippets show ~30 chars before/after the match, with `...` ellipses where truncated. Name matches always appear first.

Skips notes that already matched by name (no duplicate rows).

### Keyboard

* **↑ / ↓** — navigate `selectedIndex`.
* **Enter** — open the selected note via `onOpenNote(results[selectedIndex].note.path)`.
* **Escape** — close overlay.
* **Click** — same as Enter on that row.

## Visual structure

```tsx
<div className="search-overlay" onClick={onClose}>
  <div className="search-modal" onClick={e => e.stopPropagation()}>
    <input className="search-input" … />
    <div className="search-results">
      {results.map((r, i) => (
        <div className={`search-result ${i === selectedIndex ? 'selected' : ''}`} …>
          <span className="search-result-name">{r.note.name}</span>
          {r.snippet && <span className="search-result-snippet">{r.snippet}</span>}
        </div>
      ))}
    </div>
  </div>
</div>
```

The overlay covers the whole window (click outside = close). The modal centers a result list with name + snippet rows.

## Bug history

* [[Noted App Bugs|Bug #7]] — original implementation ran the content scan on every keystroke (no debounce), causing visible lag on large vaults. Fix: the 250ms debounce above.

## Where it's opened

* **Ctrl+P** keyboard handler in [[App Component]].
* **Search icon** in the title bar (`.title-action-btn` with magnifying-glass SVG).

## What it doesn't do

* No fuzzy match — substring only. (`include` not `fuzzy`.) `Capstone` won't match `Cpst`.
* No regex search.
* No filter-by-folder. Searches the entire vault.
* No highlighting in results beyond the surrounding snippet.

## Related

* [[FindBar Component]] — find within the open note (different feature)
* [[App Component]] — keyboard handler and visibility state
* [[Search]] — feature view
* [[Keyboard Shortcuts]]
