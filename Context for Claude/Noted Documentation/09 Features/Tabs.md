# Tabs

Multiple open notes are shown as a horizontal tab strip in the title bar. The currently-active tab is highlighted; clicking a tab switches the editor to that note; clicking the `×` closes one.

## State

All tab state lives in [[App Component]]:

```ts
const [openTabs, setOpenTabs] = useState<OpenTab[]>([])
const [activeTabIndex, setActiveTabIndex] = useState(-1)

interface OpenTab {
  path: string
  name: string
}
```

`activeTabIndex` is the index into `openTabs`. `-1` means no tab is active (initial state, or after closing the last tab).

The mismatch to watch for: `activeNote` (from [[useVault]]) and `openTabs[activeTabIndex]` should always agree. They do, because every operation that sets one also calls into the other:

* `openNote` → loads `activeNote`, may update `openTabs`.
* `switchTab` → updates `activeTabIndex`, calls `openNote`.
* `closeTab` → updates `openTabs` and `activeTabIndex`; calls `openNote` or `clearActiveNote`.

## Opening a note in a tab

Everything funnels through `openNoteInTab(path)` in [[App Component]]:

```ts
const openNoteInTab = useCallback(async (path: string) => {
  setFindVisible(false)
  await openNote(path)
  const name = notes.find(n => n.path === path)?.name ?? path.split(/[/\\]/).pop()?.replace(/\.md$/i, '') ?? 'Untitled'

  setOpenTabs(prev => {
    const existingIndex = prev.findIndex(t => t.path === path)
    if (existingIndex >= 0) {
      setActiveTabIndex(existingIndex)
      return prev                                // already open
    }
    const next = [...prev, { path, name }]
    setActiveTabIndex(next.length - 1)
    return next                                  // append new tab
  })

  setViewMode('editor')
}, [notes, openNote])
```

Three behaviors:

1. **First open** — appends to tab list, sets it active.
2. **Already open** — just switches to it.
3. **Side effect** — also forces `viewMode` to `'editor'` (so opening a note from the graph view switches you out of graph view).

## Entry points

Every place a note opens calls `openNoteInTab`:

* [[Sidebar Component]] file click → `onOpenNote(path)` → `openNoteInTab`
* [[Sidebar Component]] context menu "Open" / "Open in New Tab" → same
* [[TabBar Component]] tab click → `switchTab(index)` → `openNote(openTabs[index].path)` (already-open path: doesn't re-add)
* [[SearchBar Component]] Enter/click → `onOpenNote(path)` → `openNoteInTab`
* [[GraphView Component]] node click → `handleGraphNodeClick(id)` → `resolveLink` → `openNoteInTab(path)`
* [[Wiki Link Plugin]] click → `onLinkClick(name)` → `resolveLink(name)` → `openNoteInTab(path)`

## Closing a tab

```ts
const closeTab = useCallback((index: number) => {
  const newTabs = openTabs.filter((_, i) => i !== index)
  setOpenTabs(newTabs)

  if (index === activeTabIndex) {
    if (newTabs.length === 0) {
      setActiveTabIndex(-1)
      clearActiveNote()
    } else if (index >= newTabs.length) {
      // Closed last tab — go to new last
      setActiveTabIndex(newTabs.length - 1)
      openNote(newTabs[newTabs.length - 1].path)
    } else {
      // Closed middle tab — current index now points at the next tab
      setActiveTabIndex(index)
      openNote(newTabs[index].path)
    }
  } else if (index < activeTabIndex) {
    // Closed a tab before the active one — shift active index left
    setActiveTabIndex(activeTabIndex - 1)
  }
}, [openTabs, activeTabIndex, openNote, clearActiveNote])
```

The "what to focus next" rules:
- Closing the active tab → focus the same index (which is now the next tab), or the new last tab if we were on the end.
- Closing a tab before the active one → keep the same note active, but shift the index.
- Closing a tab after the active one → no change to active state.

## Switching tabs

```ts
const switchTab = useCallback((index: number) => {
  if (index >= 0 && index < openTabs.length) {
    setActiveTabIndex(index)
    openNote(openTabs[index].path)
  }
}, [openTabs, openNote])
```

Updates the index and re-loads the note's content. [[Editor Component]] remounts because its `key={activeNote.path}` changes.

## Multi-select deletion side effect

[[App Component]]'s `handleDeleteItems` removes any tabs whose path was deleted (or lives inside a deleted folder):

```ts
const newTabs = openTabs.filter(t => !isGone(t.path))
setOpenTabs(newTabs)
// + adjusts activeTabIndex / clears activeNote as appropriate
```

See [[Multi-Select Deletion]].

## Overflow

When many tabs are open, the tab strip scrolls horizontally (hidden scrollbar). Each tab has `min-width: 80px; max-width: 160px; flex-shrink: 0`. See [[TabBar Component]] for the CSS.

## Right-click context menu on the tab bar

Right-clicking the tab strip (but not on a specific tab) shows:
* New Note — opens the prompt modal
* New Folder — opens the prompt modal in folder mode
* Paste (if `clipboardPath` is set) — pastes into vault root

A convenience duplicate of some sidebar actions.

## Limitations

* **No drag-to-reorder.** Tab order is open-order; the user can't rearrange.
* **No middle-click close.** Only the × button closes.
* **No tab persistence across sessions.** Closing Noted forgets the tab set.
* **No keyboard tab cycling.** Ctrl+Tab / Ctrl+Shift+Tab aren't wired.

## Related

* [[TabBar Component]] — the renderer
* [[App Component]] — state + handlers
* [[Custom Title Bar]] — the layout that contains the tab strip
* [[Editor Component]] — what gets shown for the active tab
