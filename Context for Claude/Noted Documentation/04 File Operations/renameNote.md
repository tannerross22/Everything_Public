# renameNote

**Source:** `electron/fileService.ts` → `renameNote(vaultDir, oldPath, newName)`
**IPC channel:** `vault:rename`
**Renderer access:** `window.api.renameNote(vaultDir, oldPath, newName)`

> The most consequential file operation in Noted. It rewrites references in **every other note** in the vault.

## Signature

```ts
function renameNote(
  vaultDir: string,
  oldPath: string,
  newName: string
): { newPath: string; updatedCount: number }
```

## What it does

Two-phase operation:

### Phase 1 — Rename the file
```ts
const oldNameWithoutExt = path.basename(oldPath, '.md')
const newPath = path.join(path.dirname(oldPath), `${newName}.md`)
fs.renameSync(oldPath, newPath)
```

### Phase 2 — Rewrite `[[old name]]` to `[[new name]]` in every other note

```ts
const notes = listNotes(vaultDir)
const linkRegex = /\[\[([^\]]+)\]\]/g
let updatedCount = 0

for (const note of notes) {
  if (note.path === newPath) continue   // skip the renamed file itself

  const content = readNote(note.path)
  let hasChanges = false
  const newContent = content.replace(linkRegex, (match, linkText) => {
    if (linkText === oldNameWithoutExt) {
      hasChanges = true
      updatedCount++
      return `[[${newName}]]`
    }
    return match
  })

  if (hasChanges) writeNote(note.path, newContent)
}

return { newPath, updatedCount }
```

The returned `updatedCount` is the number of **link occurrences** rewritten (not the number of distinct notes touched, though one note can contain multiple matching links).

## Why this is the only file op that touches other files

Wiki links resolve by **name**, not path:

```ts
// in App.tsx resolveLink
const match = notes.find(n => n.name.toLowerCase() === linkName.toLowerCase())
```

So if you rename `Apollo.md` to `Apollo 13.md`, every existing `[[Apollo]]` reference would suddenly be a phantom link (or, in the current [[useGraph]] implementation, an invisible one). Rewriting them keeps the graph and editor in sync with what the user clearly intended.

Note that this is **exact-match**, case-sensitive (`linkText === oldNameWithoutExt`). A `[[apollo]]` link would not be updated when renaming `Apollo`. This is a known limitation.

## Watcher guard

```ts
ipcMain.handle('vault:rename', (_event, vaultDir, oldPath, newName) => {
  isWriting = true
  const result = renameNote(vaultDir, oldPath, newName)
  setTimeout(() => { isWriting = false }, 200)
  return result
})
```

200ms guard. Because Phase 2 may write many files, this guard might not suppress every chokidar event — some `files-changed` events will leak through and trigger a renderer refresh, which is fine.

## Callers

[[useVault]] `renameNote`:

```ts
const renameNote = async (oldPath: string, newName: string) => {
  if (!vaultDir || !newName.trim()) return
  const result = await window.api.renameNote(vaultDir, oldPath, newName)
  if (activeNote?.path === oldPath) {
    // Update active note's path to the new one
    setActiveNote(prev => prev ? { ...prev, path: result.newPath, name: newName } : null)
  }
  await refreshNotes()
  return result
}
```

If the user renames the file currently open in the editor, the active note is patched in-place so the tab and editor don't get confused.

Triggered by:
* [[Sidebar Component]] inline rename UI (double-click name → edit input → Enter)
* Context menu "Rename"

The Sidebar drives the input state (`renamingPath`, `renameValue`) and calls `onRenameNote(oldPath, newName)` on Enter.

## Performance

For an N-note vault, Phase 2 is O(N × file_size). On large vaults (~thousands of notes), a rename can take noticeable time. Could be optimized by:
* Skipping notes whose content doesn't contain `[[`.
* Streaming reads.
* Indexing references at startup.

None of these are implemented.

## Edge cases

* **New name collides.** `fs.renameSync` will overwrite the destination on Unix and fail on Windows. The user gets an error toast and the operation is aborted. There is no automatic collision-resolver (compare [[createNote]]'s `name 1`, `name 2` strategy).
* **Cross-folder rename.** Not supported by this function — only the basename changes; the path stays in the same directory. To rename **and** move, use [[moveNote]] after.
* **Note inside `assets/`.** Skipped by [[listNotes]], so its links wouldn't be rewritten. In practice no `.md` files should live in `assets/`.

## Related

* [[moveNote]] — change location, not name
* [[Wiki Links]]
* [[Rename and References]] — feature-level view
* [[useVault]] `renameNote`
* [[Sidebar Component]] — UI
