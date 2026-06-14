# deleteNote

**Source:** `electron/fileService.ts` → `deleteNote(filePath)`
**IPC channel:** `vault:delete`
**Renderer access:** `window.api.deleteNote(filePath)`

## Signature

```ts
function deleteNote(filePath: string): void
```

## What it does

```ts
export function deleteNote(filePath: string): void {
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath)
  }
}
```

* Silently no-ops if the file doesn't exist (idempotent).
* No recycle-bin / trash. Deleted = gone. The user is expected to use Git for undo.
* No `[[reference]]` cleanup. Other notes that link to the deleted note keep their `[[Stale Link]]` text; those links become "phantom" in the graph (or, in the current [[useGraph]] implementation, are skipped entirely).

## Watcher guard

```ts
ipcMain.handle('vault:delete', (_event, filePath) => {
  isWriting = true
  deleteNote(filePath)
  setTimeout(() => { isWriting = false }, 200)
})
```

200ms guard, no manual `files-changed` push (chokidar's `unlink` event fires it after the guard).

## Callers

Three paths end up here:

1. **Active note deletion** ([[useVault]] `deleteCurrentNote`):
   ```ts
   const deleteCurrentNote = async () => {
     if (!activeNote) return
     await window.api.deleteNote(activeNote.path)
     setActiveNote(null)
     window.api.setTitle('Noted')
     await refreshNotes()
   }
   ```
   Triggered by:
   * Delete key in [[App Component]]'s keyboard handler (when no multi-selection)
   * Sidebar `delete-btn` (the `−` button in the header, shown only when an active note exists)
   * Sidebar context menu "Delete" on the active file

2. **Folder context menu "Delete"** ([[Sidebar Component]] `handleDeleteNote`):
   Same flow but called from a right-click on a non-active file.

3. **Multi-select delete** ([[App Component]] `handleDeleteItems`):
   Iterates the user's selection and calls `window.api.deleteNote(item.path)` for each file. See [[Multi-Select Deletion]].

## Tab cleanup

When a note is deleted, any open tab pointing at it must be removed. This happens in two places:

* **Single delete:** [[App Component]] keyboard handler explicitly calls `closeTab(activeTabIndex)` before `deleteCurrentNote()`.
* **Multi-delete:** `handleDeleteItems` rebuilds the tabs array, filtering out deleted paths and any paths inside deleted folders.

## Confirmation

The renderer always prompts before calling `deleteNote`:
* Single-note: `modal.confirm` via [[useModal]] / [[Modal Component]] (older versions used `window.api.confirm` — see [[Noted App Bugs|Bug #10]]).
* Multi-select: a single batched modal: "Delete N items? This cannot be undone."

## Related

* [[deleteFolder]] — folder variant (recursive)
* [[Multi-Select Deletion]] — batched UX
* [[useVault]] `deleteCurrentNote`
* [[App Component]] `handleDeleteItems`
* [[Sidebar Component]] — UI entry points
