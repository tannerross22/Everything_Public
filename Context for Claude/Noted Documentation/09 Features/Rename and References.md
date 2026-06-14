# Rename and References

Renaming a note **also rewrites every `[[old name]]` reference in every other note** to `[[new name]]`. This is what keeps the graph and editor links coherent after a rename.

## User flow

1. Double-click a note name in the sidebar, **or** right-click → Rename.
2. The row turns into an input with the current name selected.
3. Type a new name, press Enter.
4. The file is renamed; every `[[old]]` in other notes becomes `[[new]]`.
5. If the renamed note is currently open, the tab and editor title update to the new name (no remount).

## The rename UI in Sidebar

```ts
const [renamingPath, setRenamingPath] = useState<string | null>(null)
const [renameValue, setRenameValue] = useState('')

const startRename = (node: FileTreeNode) => {
  setRenamingPath(node.path)
  setRenameValue(node.name)
}

const commitRename = async () => {
  if (!renamingPath || !renameValue.trim()) {
    setRenamingPath(null)
    return
  }
  await onRenameNote?.(renamingPath, renameValue.trim())
  setRenamingPath(null)
  setRenameValue('')
}
```

The render path checks `renamingPath === node.path` and swaps the row for an `<input>` with autofocus. Enter calls `commitRename`. Escape cancels.

## The wire to backend

`onRenameNote(oldPath, newName)` from [[Sidebar Component]] props is wired in [[App Component]] to [[useVault]]'s `renameNote`:

```ts
// in useVault
const renameNote = async (oldPath, newName) => {
  const result = await window.api.renameNote(vaultDir, oldPath, newName)
  if (activeNote?.path === oldPath) {
    setActiveNote(prev => prev ? { ...prev, path: result.newPath, name: newName } : null)
  }
  await refreshNotes()
  return result
}
```

Which IPCs to [[renameNote]] in the main process — the two-phase rename function.

## Phase 1: rename the file

```ts
const oldNameWithoutExt = path.basename(oldPath, '.md')
const newPath = path.join(path.dirname(oldPath), `${newName}.md`)
fs.renameSync(oldPath, newPath)
```

Same folder; only the basename changes.

## Phase 2: rewrite references

```ts
const linkRegex = /\[\[([^\]]+)\]\]/g
for (const note of listNotes(vaultDir)) {
  if (note.path === newPath) continue          // skip self
  const content = readNote(note.path)
  let hasChanges = false
  const newContent = content.replace(linkRegex, (match, linkText) => {
    if (linkText === oldNameWithoutExt) {
      hasChanges = true; updatedCount++
      return `[[${newName}]]`
    }
    return match
  })
  if (hasChanges) writeNote(note.path, newContent)
}
return { newPath, updatedCount }
```

* **Exact-match** comparison: `linkText === oldNameWithoutExt`. Case-sensitive, no normalization.
* Counts replacements across all files; returns `updatedCount` so the UI can surface "12 references updated."
* Each modified note is written back via [[readNote and writeNote|writeNote]].

## Asymmetry to be aware of

| Operation | Case-sensitivity |
|---|---|
| Resolving a clicked link (`resolveLink`) | **insensitive** (`toLowerCase` compare) |
| Rewriting references on rename | **sensitive** (`===` compare) |

This means `[[Apollo]]` and `[[apollo]]` both resolve to `Apollo.md` while it's named that — but renaming `Apollo` to `Saturn V` only rewrites `[[Apollo]]`, leaving `[[apollo]]` as a now-broken reference.

In practice the user rarely mixes casing, so this edge case bites infrequently. A fix would be to lowercase both sides in the rename regex too. Not done.

## When the active note is renamed

```ts
if (activeNote?.path === oldPath) {
  setActiveNote(prev => prev ? { ...prev, path: result.newPath, name: newName } : null)
}
```

The active note's path and name are updated in place — no [[Editor Component]] remount. The window title (set by [[useVault]] `openNote`) won't update until the next call (which doesn't happen on rename alone). **Known small gap.**

The open tab's name in [[TabBar Component]] does **not** update either, because tabs cache `{path, name}` snapshots. Closing and reopening the tab fixes it. **Known small gap.**

## Performance

Phase 2 is **O(N × file_size)** — every note in the vault is read and regex-scanned. For a ~thousand-note vault this is hundreds of ms; for tens of thousands it would be noticeable.

Possible optimizations (not done):
* Quick skip if `content.indexOf('[[')` is -1.
* Build a reference index at startup and update it incrementally.
* Streaming reads.

## Bugs and gotchas

* **Collision.** `fs.renameSync` overwrites on Unix, fails on Windows. There is no collision check.
* **Rename to same name.** No-op at the filesystem level; Phase 2 still runs but finds no matches (no `[[old]]` is also `[[old]]` after).
* **Untouched links.** Links inside `assets/` `.md` files (if any) aren't touched because [[listNotes]] skips that folder. In practice no `.md` lives in `assets/`.
* **Case mismatch** as discussed above.

## Related

* [[renameNote]] — the main-process implementation
* [[Wiki Links]]
* [[Sidebar Component]] — the rename UI
* [[useVault]] `renameNote`
* [[listNotes]]
