# Search

Vault-wide search overlay opened with **Ctrl+P** or the search icon in the title bar. Matches both note **names** (instant) and note **content** (debounced 250ms).

## UX

* Press **Ctrl+P**. The search overlay appears with the input focused.
* Empty query shows every note (so the overlay doubles as a command palette).
* Type — name matches appear instantly.
* After 250ms of pause, content matches with snippets append below.
* **↑ / ↓** navigate; **Enter** opens; **Escape** closes; click works too.

## Implementation

Entirely inside [[SearchBar Component]]. The component receives the flat `notes[]` array from [[useVault]] and:

1. **Name search** — synchronous `Array.filter` on every keystroke. ~free for thousands of notes.
2. **Content search** — debounced 250ms. After the pause, iterates every note that didn't already match by name, reads its content via [[readNote and writeNote|readNote]], does an `indexOf(query)`. If found, builds a ~60-character snippet around the match.

```ts
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

## Why 250ms

* Long enough for the user to finish typing several characters.
* Short enough that the snippet results appear before the user gives up waiting.

Originally the content scan ran on every keystroke — [[Noted App Bugs|Bug #7]] documented the resulting lag on larger vaults. The debounce fixed it.

## Bottleneck

For a 10000-note vault, each content scan does 10000 IPC roundtrips. That's where the debounce matters most — without it, you'd be issuing tens of thousands of IPC calls per second while typing.

A future optimization would maintain an in-memory search index. None is currently implemented.

## What this doesn't do

* **No fuzzy matching.** Substring `indexOf` only. `[[Apollo]]` won't match `aplo`.
* **No regex.**
* **No "in folder" filter.**
* **No tag search** (there are no tags).
* **No "this word but not that word."**

## Visual

The overlay is centered on the window, ~600px wide, with a list of matches below the input. Each row shows the note name (bold) and the snippet (dim) when present. Hovering a row updates `selectedIndex` so Enter opens what you're hovering.

## Related

* [[SearchBar Component]] — the component
* [[FindBar Component]] — different feature (find in current note, Ctrl+F)
* [[App Component]] — Ctrl+P handler, `searchVisible` state
* [[Keyboard Shortcuts]]
* [[Noted App Bugs|Bug #7]]
