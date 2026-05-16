# createFolder and deleteFolder

## createFolder

**Source:** `electron/fileService.ts` → `createFolder(folderPath)`
**IPC channel:** `vault:createFolder`
**Renderer access:** `window.api.createFolder(folderPath)`

```ts
export function createFolder(folderPath: string): string {
  if (!fs.existsSync(folderPath)) {
    fs.mkdirSync(folderPath, { recursive: true })
  }
  return folderPath
}
```

* `recursive: true` — multiple missing ancestors get created in one call.
* Idempotent if the folder already exists.

### Callers
* [[useVault]] `createFolder` → triggered by:
  * Sidebar header "+ folder" button (→ inline input → `pathJoin(vaultDir, name)`)
  * Sidebar context menu "New Folder Here"
  * "+ folder" prompt modal in [[App Component]]

### Auto-color assignment

When the new folder is a [[useFolderColors|top-level folder]] (direct child of `vaultDir`), [[App Component]]'s `handleCreateFolder` assigns it a color from the palette:

```ts
const handleCreateFolder = (fullPath: string) => {
  createFolder(fullPath)
  if (vaultDir && isTopLevelFolder(fullPath, vaultDir)) {
    const color = assignFolderColor(fullPath)
    setFolderColors(prev => ({ ...prev, [fullPath]: color }))
  }
}
```

See [[Folder Colors]].

---

## deleteFolder

**Source:** `electron/fileService.ts` → `deleteFolder(folderPath)`
**IPC channel:** `vault:deleteFolder`
**Renderer access:** `window.api.deleteFolder(folderPath)`

```ts
export function deleteFolder(folderPath: string): void {
  fs.rmSync(folderPath, { recursive: true, force: true })
}
```

* `recursive: true` — wipes all descendants.
* `force: true` — doesn't error on missing folder.
* **No trash.** Same as [[deleteNote]] — deleted = gone.

### Watcher guard

The IPC handler in [[main.ts]] uses a **500ms guard** (longer than [[deleteNote]]'s 200ms) because folder deletion typically produces many chokidar `unlink`/`unlinkDir` events:

```ts
ipcMain.handle('vault:deleteFolder', (_event, folderPath) => {
  isWriting = true
  deleteFolder(folderPath)
  setTimeout(() => { isWriting = false }, 500)
})
```

### Callers

* [[useVault]] `deleteFolder` — wraps the IPC call and additionally clears the active note if it lived inside the deleted folder:

```ts
const deleteFolder = async (folderPath: string) => {
  await window.api.deleteFolder(folderPath)
  if (activeNote) {
    const sep = folderPath.includes('\\') ? '\\' : '/'
    if (activeNote.path.startsWith(folderPath + sep)) {
      setActiveNote(null)
      window.api.setTitle('Noted')
    }
  }
  await refreshNotes()
}
```

* [[App Component]] `handleDeleteItems` — calls `window.api.deleteFolder` directly when a folder is in the multi-select set. Also cleans up open tabs inside the deleted folder. See [[Multi-Select Deletion]].

### Confirmation

The user always confirms via [[Modal Component]] before deletion:

> "Delete folder \"Projects\" and everything inside it? This cannot be undone."

Or, in multi-select:

> "Delete N selected items? This cannot be undone."

## Related

* [[deleteNote]]
* [[Multi-Select Deletion]]
* [[Folder Colors]]
* [[useVault]] `deleteFolder`
* [[Sidebar Component]] — context menu
