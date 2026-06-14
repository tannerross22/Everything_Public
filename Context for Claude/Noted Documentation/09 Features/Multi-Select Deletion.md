# Multi-Select Deletion

Allow the user to Ctrl-click or Shift-click multiple files/folders in the sidebar, then delete all of them in one operation.

## User interactions

| Action | Effect |
|---|---|
| **Click** | Replace selection, run default action (open note / toggle folder) |
| **Ctrl/Cmd-click** | Toggle this item in/out of the selection; don't open |
| **Shift-click** | Range-select from the last item to this one (inclusive) |
| **Click empty space in sidebar** | Clear selection |
| **Right-click → Delete Selected (N)** | Confirm + delete all selected |
| **Header trash button (with count badge)** | Same as Delete Selected |
| **Delete key (when ≥2 selected)** | Same as Delete Selected |

When 1 item is selected, the Delete key still goes through the standard "delete active note" flow (not multi-delete). Two-or-more is the threshold for multi-delete.

## State location

Multi-select state is **lifted to [[App Component]]**:

```ts
const [sidebarSelectedPaths, setSidebarSelectedPaths] = useState<Set<string>>(new Set())
```

This is needed because the **Delete key handler** in App needs to know whether multi-select is active. The sidebar can't own that state alone unless it also intercepts keyboard events, which would clash with App's global handler.

[[Sidebar Component]] receives the set as a prop (`selectedPaths`) and the setter (`onSelectionChange`). The "last selected" for shift-click range stays local to the sidebar.

## Selection click handler (in Sidebar)

```ts
const handleNodeClick = (e: React.MouseEvent, node: FileTreeNode, defaultAction: () => void) => {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    const next = new Set(selectedPaths)
    next.has(node.path) ? next.delete(node.path) : next.add(node.path)
    onSelectionChange(next)
    setLastSelectedPath(node.path)
  } else if (e.shiftKey && lastSelectedPath) {
    e.preventDefault()
    const flat = flattenVisible(fileTree, expanded)
    const lastIdx = flat.findIndex(n => n.path === lastSelectedPath)
    const thisIdx = flat.findIndex(n => n.path === node.path)
    if (lastIdx >= 0 && thisIdx >= 0) {
      const [from, to] = lastIdx <= thisIdx ? [lastIdx, thisIdx] : [thisIdx, lastIdx]
      onSelectionChange(new Set(flat.slice(from, to + 1).map(n => n.path)))
    }
  } else {
    onSelectionChange(new Set([node.path]))
    setLastSelectedPath(node.path)
    defaultAction()
  }
}
```

* **`flattenVisible`** — walks the file tree in display order including only expanded descendants. The flattened order is what defines a "range" for shift-click.
* **`lastSelectedPath`** — the most recently clicked path; the anchor for shift-click.

## Delete handler — `handleDeleteItems` in App

```ts
const handleDeleteItems = useCallback(async (items) => {
  if (items.length === 0) return

  // Confirm
  const confirmed = await modal.confirm({
    title: `Delete ${items.length} Item${items.length > 1 ? 's' : ''}`,
    message: `Delete ${items.length} selected item${items.length > 1 ? 's' : ''}? This cannot be undone.`,
    confirmText: 'Delete',
    cancelText: 'Cancel',
    isDangerous: true,
  })
  if (!confirmed) return

  // Dedupe: skip items inside a selected folder
  const folderPaths = items.filter(i => i.type === 'folder').map(i => i.path)
  const toDelete = items.filter(item =>
    !folderPaths.some(fp =>
      item.path !== fp &&
      (item.path.startsWith(fp + '\\') || item.path.startsWith(fp + '/'))
    )
  )

  // Delete via IPC
  for (const item of toDelete) {
    if (item.type === 'folder') await window.api.deleteFolder(item.path)
    else                        await window.api.deleteNote(item.path)
  }

  // Close affected tabs
  const isGone = (path) =>
    toDelete.some(i => i.path === path) ||
    folderPaths.some(fp => path.startsWith(fp + '\\') || path.startsWith(fp + '/'))

  const currentTab = openTabs[activeTabIndex]
  const newTabs = openTabs.filter(t => !isGone(t.path))
  setOpenTabs(newTabs)

  if (newTabs.length === 0) {
    setActiveTabIndex(-1); clearActiveNote()
  } else if (currentTab && isGone(currentTab.path)) {
    const newIdx = Math.min(activeTabIndex, newTabs.length - 1)
    setActiveTabIndex(newIdx)
    openNote(newTabs[newIdx].path)
  } else if (currentTab) {
    const newIdx = newTabs.findIndex(t => t.path === currentTab.path)
    if (newIdx >= 0) setActiveTabIndex(newIdx)
  }

  setSidebarSelectedPaths(new Set())
  await refreshNotes()
}, [modal, openTabs, activeTabIndex, openNote, clearActiveNote, refreshNotes])
```

Three rounds of cleanup:

1. **Dedupe.** If both a folder and a file inside it are selected, the folder delete handles the file — no need (and dangerous) to delete the file separately first.
2. **Delete.** Loop calling [[deleteFolder]] or [[deleteNote]] per item.
3. **Tab cleanup.** Remove any tabs whose path was deleted or whose path is inside a deleted folder. Adjust `activeTabIndex` so the new active tab is valid.

After all this, clear the selection and refresh the note list.

## Delete key wiring (in App keyboard handler)

```ts
if (!isEditing && e.key === 'Delete') {
  if (sidebarSelectedPaths.size > 1) {
    e.preventDefault()
    // Build items[] from selected paths by looking up types in the sorted tree
    const allNodes = []
    const flatten = (nodes) => { for (const n of nodes) { allNodes.push(n); if (n.children) flatten(n.children) } }
    flatten(sortedFileTree)
    const pathTypeMap = new Map(allNodes.map(n => [n.path, n.type]))
    const items = Array.from(sidebarSelectedPaths).map(p => ({
      path: p,
      type: pathTypeMap.get(p) ?? 'file',
    }))
    handleDeleteItems(items)
  } else if (activeNote) {
    e.preventDefault()
    modal.confirm({ title: 'Delete Note', message: `Delete "${activeNote.name}"? …`, isDangerous: true, … })
      .then(ok => { if (ok) { closeTab(activeTabIndex); deleteCurrentNote() } })
  }
}
```

When ≥2 items are selected, the Delete key uses `handleDeleteItems`. Otherwise it deletes the active note via [[useVault]] `deleteCurrentNote`.

## Visual states

```css
.sidebar-note.selected,
.sidebar-folder-row.selected {
  background: rgba(203, 166, 247, 0.12);
  outline: 1px solid rgba(203, 166, 247, 0.25);
  outline-offset: -1px;
}

.sidebar-note.active.selected {
  background: var(--bg-surface);            /* active wins for bg */
  outline: 1px solid rgba(203, 166, 247, 0.4);
}
```

A purple-tinted background + outline. The active note takes precedence on background color.

The header gets a `.multi-delete-btn` with a count badge when `selectedPaths.size > 1`:

```tsx
{selectedPaths.size > 1 && (
  <button className="sidebar-btn icon-btn delete-btn multi-delete-btn"
          onClick={() => handleDeleteSelected()}
          title={`Delete ${selectedPaths.size} selected items`}>
    <svg>{/* trash icon */}</svg>
    <span>{selectedPaths.size}</span>
  </button>
)}
```

## Selection clearing

Selection is cleared:

* After a successful `handleDeleteItems`.
* When the vault changes (`useEffect` on `vaultDir`).
* When clicking sidebar background (event target === currentTarget).
* When clicking the empty area of the file tree (same trick).

Not cleared on Escape — would be a reasonable future addition.

## Related

* [[Sidebar Component]] — click handling
* [[App Component]] — `handleDeleteItems`, keyboard handler
* [[deleteNote]], [[deleteFolder]] — underlying ops
* [[useModal]] — confirmation dialog
* [[Tabs]] — tab cleanup after delete
