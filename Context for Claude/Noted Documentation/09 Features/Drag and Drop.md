# Drag and Drop

Drag any file or folder in the [[Sidebar Component]] onto a target folder to move it. Drag onto the root area of the file tree to move it to the vault root.

## State

```ts
const [draggingPath, setDraggingPath] = useState<string | null>(null)
const [dragOverPath, setDragOverPath] = useState<string | null>(null)
```

* `draggingPath` — the item being dragged. Applies `.dragging` class (faded opacity).
* `dragOverPath` — the current hover target. Applies `.drag-over` class to the folder being hovered, or `.drag-over-root` to the notes container.

## Handlers

### `handleDragStart`

```ts
const handleDragStart = (e: React.DragEvent, path: string) => {
  setDraggingPath(path)
  e.dataTransfer.setData('text/plain', path)
  e.dataTransfer.effectAllowed = 'move'
}
```

Stores the source path in the native dataTransfer (for future cross-window drops, though Noted has only one window).

### `handleDragOver`

```ts
const handleDragOver = (e: React.DragEvent, targetPath: string) => {
  e.preventDefault()
  setDragOverPath(targetPath)
  e.dataTransfer.dropEffect = 'move'
}
```

`preventDefault` is required for the drop to be allowed by the browser. Updates the hover target for visual feedback.

### `handleDrop`

```ts
const handleDrop = (e: React.DragEvent, targetPath: string) => {
  e.preventDefault()
  const sourcePath = e.dataTransfer.getData('text/plain')
  setDraggingPath(null)
  setDragOverPath(null)

  // The notes-container drop resolves to vaultDir
  const resolvedTarget = targetPath === '__root__' ? vaultDir : targetPath

  if (!sourcePath || sourcePath === resolvedTarget) return

  // Guard against dropping into self / descendant
  const sep = sourcePath.includes('\\') ? '\\' : '/'
  if (resolvedTarget.startsWith(sourcePath + sep)) return

  onMoveItem(sourcePath, resolvedTarget)
}
```

Three guards:

1. **No source.** Drag wasn't from the sidebar (e.g. from another app).
2. **Source equals target.** Drop onto self — no-op.
3. **Target is a descendant of source.** Would create a recursive move (moving `A` into `A/sub/`). Prevented.

## Drop targets

* **Any folder row** in the tree → drops the source into that folder.
* **The whole `.sidebar-notes` container** (when dragged onto empty space) → drops into the vault root.

The second case uses the sentinel `targetPath === '__root__'` in the hover handler so we can distinguish "hover the root area" from "hover a specific folder."

## What "move" means

`onMoveItem` in [[Sidebar Component]] props is wired in [[App Component]] to `moveItem` from [[useVault]]:

```ts
const moveItem = useCallback(async (oldPath, newFolderPath) => {
  await window.api.moveNote(oldPath, newFolderPath)
  await refreshNotes()
}, [refreshNotes])
```

Which calls [[moveNote]]'s IPC channel and triggers a sidebar refresh.

## Wiki links are not rewritten

Moving a note does **not** rewrite `[[references]]` anywhere — because wiki link resolution is **by name, not by path**. As long as `Apollo.md` exists somewhere in the vault, every `[[Apollo]]` still resolves correctly.

Compare with [[renameNote]], which changes the name and **must** rewrite references.

## Cross-volume moves

`fs.renameSync` in [[moveNote]] handles cross-volume moves via Node's internal copy+delete. Works for typical desktop usage.

## What you can't drag

* **Multiple selected items.** The drag mechanism uses native HTML5 drag, which only transfers one item. Multi-select drag would need a custom implementation. Not done.
* **Items into the editor.** Editor is unaware of sidebar drag events.

## Related

* [[moveNote]] — the underlying IPC + fs call
* [[useVault]] `moveItem`
* [[Sidebar Component]] — the drag-source and drop-target host
