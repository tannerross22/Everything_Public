# copyItem

**Source:** `electron/fileService.ts` → `copyItem(sourcePath, destFolder)`
**IPC channel:** `vault:copyItem`
**Renderer access:** `window.api.copyItem(sourcePath, destFolder)`

## Signature

```ts
function copyItem(sourcePath: string, destFolder: string): string  // returns new path
```

## What it does

Copies a file or folder into `destFolder`, auto-renaming on conflict.

```ts
let destPath = path.join(destFolder, path.basename(sourcePath))

// Conflict resolution: append (copy), (copy 2), (copy 3), …
if (fs.existsSync(destPath)) {
  const ext = path.extname(basename)
  const nameNoExt = path.basename(basename, ext)
  let i = 1
  do {
    const suffix = i === 1 ? ' (copy)' : ` (copy ${i})`
    destPath = path.join(destFolder, `${nameNoExt}${suffix}${ext}`)
    i++
  } while (fs.existsSync(destPath))
}

const stat = fs.statSync(sourcePath)
if (stat.isDirectory()) {
  fs.cpSync(sourcePath, destPath, { recursive: true })
} else {
  fs.copyFileSync(sourcePath, destPath)
}
```

* **Files:** `fs.copyFileSync` — straight byte copy.
* **Folders:** `fs.cpSync(..., { recursive: true })` — recursively copies every descendant.
* **Collision strategy:** `My Note.md` → `My Note (copy).md` → `My Note (copy 2).md` → …

This differs from [[createNote]]'s strategy (which uses `name 1`, `name 2`). The "(copy)" naming is consistent with OS file managers.

## Watcher guard

```ts
ipcMain.handle('vault:copyItem', (_event, sourcePath, destFolder) => {
  isWriting = true
  const result = copyItem(sourcePath, destFolder)
  setTimeout(() => { isWriting = false }, 500)
  return result
})
```

**500ms** guard (longer than the default 200ms) because folder copies fire many chokidar events.

## Callers

[[App Component]] `handlePaste`:

```ts
const handlePaste = useCallback(async (destFolder: string) => {
  if (!clipboardPath) return
  await window.api.copyItem(clipboardPath, destFolder)
  await refreshNotes()
}, [clipboardPath, refreshNotes])
```

The "clipboard" is just an in-memory `clipboardPath: string | null` in [[App Component]] — not the OS clipboard. Right-click "Copy" on a sidebar item populates it; right-click "Paste" calls `handlePaste(destFolder)`.

See [[Copy and Paste]] for the UX.

## Why is this called "copyItem", not "copyNote"?

Because it handles **both** files and folders (and pasting whole folders is a supported use case). The same pattern with [[moveNote]] keeps its narrower name for historical reasons.

## Edge cases

* **Source no longer exists.** `fs.statSync` throws — the IPC handler rejects, the renderer's `await` rejects, currently no error toast in the renderer (silently fails).
* **Cross-volume copy.** Works (it's a true copy, not a rename).
* **Copy onto self / into descendant.** Not specifically guarded against — would produce a recursive copy until the disk fills (in theory). Drag-and-drop has a separate guard against this; right-click copy/paste does not.

## Related

* [[moveNote]] — destructive variant
* [[Copy and Paste]]
* [[App Component]] `handlePaste`, `clipboardPath`
* [[Sidebar Component]] — Copy/Paste context menu items
