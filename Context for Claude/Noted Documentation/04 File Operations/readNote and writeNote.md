# readNote and writeNote

The two functions that move a single note's content across the disk boundary.

## readNote

**Source:** `electron/fileService.ts` → `readNote(filePath)`
**IPC channel:** `vault:read`
**Renderer access:** `window.api.readNote(filePath)`

```ts
export function readNote(filePath: string): string {
  return fs.readFileSync(filePath, 'utf-8')
}
```

Synchronous on the disk side, but the **IPC wrapping** makes it `Promise<string>` to the renderer. The whole file is read into memory. There is no streaming; for the ~kilobyte text files Noted handles this is fine.

### Callers
* [[useVault]] `openNote` — load content when a note is selected
* [[useVault]] `onFilesChanged` callback — re-read the active note after an external change
* [[SearchBar Component]] — read every note to do content search
* [[useGraph]] — read every note to scan for `[[wiki links]]`

## writeNote

**Source:** `electron/fileService.ts` → `writeNote(filePath, content)`
**IPC channel:** `vault:write`
**Renderer access:** `window.api.writeNote(filePath, content)`

```ts
export function writeNote(filePath: string, content: string): void {
  const dir = path.dirname(filePath)
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true })
  }
  fs.writeFileSync(filePath, content, 'utf-8')
}
```

* Idempotent on directory creation: if the parent folder doesn't exist, it's created recursively. (Important when notes are moved/renamed.)
* `fs.writeFileSync` is atomic on most platforms — the file is either fully written or untouched.

### The watcher guard

The IPC handler in [[main.ts]] does **more** than just call `writeNote`:

```ts
ipcMain.handle('vault:write', async (_event, filePath, content) => {
  isWriting = true                                    // suppress watcher
  writeNote(filePath, content)
  setTimeout(() => {
    isWriting = false
    mainWindow?.webContents.send('vault:files-changed')  // manual fire-after-write
  }, 200)
})
```

This is the self-write guard pattern (see [[File Watcher]]). Without it, the chokidar `change` event from our own write would trigger a `vault:files-changed` event, which would re-fetch state we already know about.

### Callers
The only caller in the codebase is [[useVault]] `saveNote` (called by `updateContent`, debounced 100ms). Conceptually this is the [[Autosave]] pipeline.

`writeNote` is also called **internally** in main from [[renameNote]] (when rewriting `[[references]]` in other files after a rename).

## Why both are synchronous on the disk side

`fs.readFileSync` and `fs.writeFileSync` block the Node event loop, but:
* The main process is dedicated to file I/O — it has no UI to keep responsive.
* For sub-MB files the block is <10ms.
* IPC handlers return promises regardless; the renderer never sees the sync.

Switching to `fs.promises` would add overhead without changing observable behavior.

## Related

* [[Data Flow]] — Trace 1 walks through a save end-to-end
* [[Autosave]] — the 100ms debounce strategy
* [[useVault]] — caller side
* [[File Watcher]] — why the post-write `isWriting` guard exists
