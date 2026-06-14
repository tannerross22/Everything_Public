# Sidebar Component

**Path:** `src/components/Sidebar.tsx`

The file-tree pane on the left. Largest component by far (~660 lines): it owns the file tree rendering, inline create/rename UI, drag-and-drop, context menus, and the footer with vault label + sync button.

Selection state and the multi-delete handler live in [[App Component]] and are passed down as props.

## Props

```ts
interface SidebarProps {
  fileTree: FileTreeNode[]
  activeNotePath: string | null
  activeNoteName: string | null

  // File ops
  onOpenNote: (path: string) => void | Promise<void>
  onOpenNoteInNewTab: (path: string) => Promise<void>
  onCreateNote: (name: string, folderPath?: string) => void
  onCreateFolder: (fullPath: string) => void
  onDeleteFolder: (folderPath: string) => void
  onDeleteNote?: () => void
  onMoveItem: (oldPath: string, newFolderPath: string) => void
  onChangeVault: () => void
  onRenameNote?: (oldPath: string, newName: string) => Promise<any>

  // Vault context
  vaultDir: string
  folderColors: Record<string, string>

  // Clipboard
  clipboardPath: string | null
  onCopy: (path: string) => void
  onPaste: (destFolder: string) => void

  // Modal confirm
  onConfirm?: (config: ModalConfig) => Promise<boolean>

  // Git sync (from useGitSync via App)
  isRepo: boolean
  hasChanges: boolean
  syncing: boolean
  isProcessing: boolean
  showSynced: boolean
  onSync: () => void

  // Multi-select (lifted to App)
  selectedPaths: Set<string>
  onSelectionChange: (paths: Set<string>) => void
  onDeleteItems: (items: Array<{ path: string; type: 'file' | 'folder' }>) => Promise<void>

  // Layout
  style?: React.CSSProperties
  className?: string
}
```

## Local state

```ts
const [expanded, setExpanded] = useState<Set<string>>(new Set())   // open folders
const [draggingPath, setDraggingPath] = useState<string | null>(null)
const [dragOverPath, setDragOverPath] = useState<string | null>(null)
const [creating, setCreating] = useState<CreatingState>(null)       // inline new-note/folder input
const [createValue, setCreateValue] = useState('')
const [renamingPath, setRenamingPath] = useState<string | null>(null)
const [renameValue, setRenameValue] = useState('')
const [ctxMenu, setCtxMenu] = useState<CtxMenu>(null)
const [lastSelectedPath, setLastSelectedPath] = useState<string | null>(null)  // for shift-click range
```

## `renderNode(node, depth, inheritedColor?)`

The recursive tree renderer. For each node:

* Resolves the icon color: top-level folders use their assigned palette color from `folderColors` (see [[useFolderColors]]); descendants inherit; everything else uses `DULL_COLOR`.
* Renders a `.sidebar-folder-row` for folders (with chevron `▾`/`▸`) or a `.sidebar-note` for files.
* Adds CSS classes `active`, `selected`, `dragging`, `drag-over` conditionally.
* Wires up `onClick`, `onContextMenu`, drag handlers.
* If the node is being renamed (`renamingPath === node.path`), swaps the row for an `<input>` with autofocus.
* If the node is a folder and `expanded.has(node.path)`, recurses into children.

## Click behavior — `handleNodeClick`

Three modes, dispatched by modifier keys:

```ts
const handleNodeClick = (e, node, defaultAction) => {
  if (e.ctrlKey || e.metaKey) {
    // Toggle this item in selection
    const next = new Set(selectedPaths)
    next.has(node.path) ? next.delete(node.path) : next.add(node.path)
    onSelectionChange(next)
    setLastSelectedPath(node.path)
  } else if (e.shiftKey && lastSelectedPath) {
    // Range select between lastSelectedPath and node.path
    const flat = flattenVisible(fileTree, expanded)
    const lastIdx = flat.findIndex(n => n.path === lastSelectedPath)
    const thisIdx = flat.findIndex(n => n.path === node.path)
    if (lastIdx >= 0 && thisIdx >= 0) {
      const [from, to] = lastIdx <= thisIdx ? [lastIdx, thisIdx] : [thisIdx, lastIdx]
      onSelectionChange(new Set(flat.slice(from, to + 1).map(n => n.path)))
    }
  } else {
    // Normal click: replace selection, run default action
    onSelectionChange(new Set([node.path]))
    setLastSelectedPath(node.path)
    defaultAction()   // file: open; folder: toggle expand
  }
}
```

`flattenVisible` is a helper that walks the tree in display order, including only the visible (expanded) descendants. That ordering defines the "range" for shift-click. See [[Multi-Select Deletion]].

## Drag and drop

* `handleDragStart(e, path)` — sets `draggingPath` and `e.dataTransfer.setData('text/plain', path)`.
* `handleDragOver(e, targetPath)` — sets `dragOverPath` so the target folder highlights.
* `handleDrop(e, targetPath)` — guards against dropping onto self or into a descendant, then calls `onMoveItem(src, targetPath)`. Detail in [[Drag and Drop]].

The whole `.sidebar-notes` container is also a drop target (`targetPath === '__root__'` for hover state; resolves to `vaultDir` on drop) so the user can drag items back to the root.

## Inline create

When the user clicks "+" or right-clicks "New Note Here":

1. `startCreating('note', parentPath)` sets `creating` state.
2. If `parentPath` is not the vault root, the parent folder is auto-expanded.
3. The tree renders an `<input>` inline at the right depth (`renderCreateInput`).
4. Enter commits via `onCreateNote(value, parentPath)` (or `onCreateFolder` for folders).
5. Blur or Escape cancels.

## Inline rename

Same pattern. `startRename(node)` sets `renamingPath` + `renameValue`. `renderNode` checks `isRenaming` and renders an input instead of the row. Commit on Enter / blur; cancel on Escape. Calls `onRenameNote(oldPath, newName)` — see [[Rename and References]].

## Context menu

`openCtxMenu(e, node)` stores `{ x, y, node }`. The render block at the bottom checks this state and shows:

* **Empty space:** New Note, New Folder, (Paste if clipboardPath set).
* **Folder node:** New Note Here, New Folder Here, Copy, (Paste), Rename, Delete Folder, (Delete Selected if >1 selected).
* **File node:** Open, Open in New Tab, Copy, Rename, Delete, (Delete Selected if >1 selected).

The menu closes on any click that bubbles to the sidebar root or on Escape.

## Header buttons

| Button | Shown when | Action |
|---|---|---|
| Multi-delete (icon + count) | `selectedPaths.size > 1` | Calls `handleDeleteSelected()` → builds items, calls `onDeleteItems` |
| Delete current (`−`) | `onDeleteNote` provided AND `activeNoteName` set | Confirms then calls `onDeleteNote` |
| New Note (icon) | Always | `startCreating('note', vaultDir)` |
| New Folder (icon) | Always | `startCreating('folder', vaultDir)` |

## Footer

```tsx
<div className="sidebar-footer">
  <button className="sidebar-btn vault-btn" onClick={onChangeVault}>
    <div className="folder-icon" />
    {vaultLabel}                      {/* basename of vaultDir */}
  </button>
  {isRepo && (
    <button className="sidebar-btn sync-btn …" onClick={onSync}
            disabled={syncing || isProcessing || !hasChanges}>
      {showSynced ? 'Synced' : 'Sync'}
    </button>
  )}
</div>
```

The Sync button mirrors the compact rail icon — both are wired to the same `handleSync` from [[useGitSync]] in [[App Component]].

## Related

* [[App Component]] — owns the props/state passed in
* [[Multi-Select Deletion]] — selection logic
* [[Drag and Drop]]
* [[Rename and References]]
* [[Copy and Paste]]
* [[Folder Colors]]
* [[useFolderColors]] — color resolution helper
* [[Sidebar Resize and Collapse]]
