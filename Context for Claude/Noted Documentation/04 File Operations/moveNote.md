# moveNote

**Source:** `electron/fileService.ts` → `moveNote(oldPath, newFolderPath)`
**IPC channel:** `vault:moveNote`
**Renderer access:** `window.api.moveNote(oldPath, newFolderPath)`

## Signature

```ts
function moveNote(oldPath: string, newFolderPath: string): string  // returns new path
```

## What it does

Moves a file or folder from its current location into a destination folder (keeping the basename). The function is named `moveNote` but it works for any file system entry — including folders — because [[useVault]] passes a generic `moveItem`.

```ts
export function moveNote(oldPath: string, newFolderPath: string): string {
  const fileName = path.basename(oldPath)
  const newPath = path.join(newFolderPath, fileName)

  if (!fs.existsSync(newFolderPath)) {
    fs.mkdirSync(newFolderPath, { recursive: true })
  }

  fs.renameSync(oldPath, newPath)
  return newPath
}
```

* `fs.renameSync` is an OS-level move — atomic on the same filesystem volume, falls back to copy+delete across volumes (handled by Node).
* The destination folder is created if missing.
* **No reference rewriting.** Wiki links (`[[Foo]]`) reference notes by name, not path, so moving doesn't break links. (Compare with [[renameNote]], which **does** rewrite references because the name changes.)

## Watcher guard

```ts
ipcMain.handle('vault:moveNote', (_event, oldPath, newFolderPath) => {
  return moveNote(oldPath, newFolderPath)
})
```

> ⚠ Interestingly, this handler does **not** set `isWriting`. The move produces both an `add` and an `unlink` chokidar event; both will arrive at the renderer as `vault:files-changed`, which is harmless (just a refresh). This is a deliberate choice or an oversight depending on perspective.

## Callers

[[useVault]] `moveItem`:

```ts
const moveItem = async (oldPath: string, newFolderPath: string) => {
  await window.api.moveNote(oldPath, newFolderPath)
  await refreshNotes()
}
```

Triggered by **drag and drop** in the [[Sidebar Component]]:

```ts
const handleDrop = (e, targetPath) => {
  …
  onMoveItem(src, targetPath)
}
```

The drop target is always a folder path (or `vaultDir` when dropping on the root area). If the user drops a file onto another file, no move occurs (the `targetPath` would be the file's path, and the check `targetPath.startsWith(src + sep)` filters out self-moves).

## Drag-and-drop guards

[[Sidebar Component]]'s `handleDrop` guards against:
* Dropping an item onto itself (`src === targetPath`).
* Dropping a folder into its own descendant (`targetPath.startsWith(src + sep)`).

Without the second guard, the user could drag `Projects/` into `Projects/Apollo/`, creating a recursive loop on disk.

## Related

* [[renameNote]] — distinct because it changes the **name** (and thus rewrites references)
* [[copyItem]] — non-destructive variant
* [[Drag and Drop]] — UX flow
* [[useVault]] `moveItem`
* [[Sidebar Component]] — drag handlers
