# useVault

**Path:** `src/hooks/useVault.ts`

The central hook for all vault-aware state. Owns `vaultDir`, the flat `notes[]` list, the `fileTree`, and the `activeNote`. Wraps every [[File Operations|file operation]] IPC. Implements the debounced [[Autosave]].

Used by [[App Component]] (and only there) to derive everything else.

## Returned API

```ts
return {
  vaultDir,               // string
  notes,                  // NoteFile[]      (flat list)
  fileTree,               // FileTreeNode[]  (hierarchy)
  activeNote,             // NoteContent | null
  openNote,               // (path) => Promise<void>
  updateContent,          // (markdown) => void   — debounced save
  createNewNote,          // (name, folderPath?) => Promise<string | undefined>
  deleteCurrentNote,      // () => Promise<void>
  changeVaultDir,         // () => Promise<void>
  renameNote,             // (oldPath, newName) => Promise<{newPath, updatedCount} | undefined>
  createFolder,           // (fullPath) => Promise<void>
  deleteFolder,           // (folderPath) => Promise<void>
  moveItem,               // (oldPath, newFolderPath) => Promise<void>
  resolveLink,            // (linkName) => Promise<string | undefined>
  refreshNotes,           // () => Promise<void>
  clearActiveNote,        // () => void
}
```

## State

```ts
const [vaultDir, setVaultDir] = useState<string>('')
const [notes, setNotes] = useState<NoteFile[]>([])
const [fileTree, setFileTree] = useState<FileTreeNode[]>([])
const [activeNote, setActiveNote] = useState<NoteContent | null>(null)
const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
```

## Bootstrap

```ts
useEffect(() => {
  window.api.getVaultDir().then(setVaultDir)
}, [])
```

On mount, asks main for the persisted vault path (via [[Vault Configuration]]). The downstream `refreshNotes` effect fires once `vaultDir` is set.

## `refreshNotes()`

```ts
const refreshNotes = useCallback(async () => {
  if (!vaultDir) return
  const [noteList, tree] = await Promise.all([
    window.api.listNotes(vaultDir),
    window.api.buildFileTree(vaultDir),
  ])
  setNotes(noteList)
  setFileTree(tree)
}, [vaultDir])

useEffect(() => { refreshNotes() }, [refreshNotes])
```

Two parallel IPC calls: [[listNotes]] for the flat list (graph/search) and [[buildFileTree]] for the hierarchy (sidebar). Re-runs whenever `vaultDir` changes — triggered by `changeVaultDir` after the user picks a new folder.

## File-watcher subscription

```ts
useEffect(() => {
  const unsubscribe = window.api.onFilesChanged(() => {
    refreshNotes()
    if (activeNote) {
      window.api.readNote(activeNote.path).then(content => {
        setActiveNote(prev => prev ? { ...prev, content } : null)
      }).catch(() => setActiveNote(null))
    }
  })
  return unsubscribe
}, [refreshNotes, activeNote?.path])
```

On every `vault:files-changed` event from [[File Watcher]]:
1. Refresh the flat list + tree.
2. If a note is open, re-read it (graceful fallback to null if it was deleted externally).

> Caveat: re-reading `activeNote.content` updates the React state, but [[Editor Component]] only reads `defaultValueCtx` at mount — Milkdown doesn't observe content updates. So external edits to the open note don't refresh visually until the user switches tabs. This is a known gap.

## `openNote(path)`

```ts
const openNote = useCallback(async (filePath) => {
  const content = await window.api.readNote(filePath)
  const name = filePath.split(/[/\\]/).pop()?.replace(/\.md$/, '') || ''
  setActiveNote({ name, path: filePath, content })
  window.api.setTitle(`Noted - ${name}`)
}, [])
```

Reads file via [[readNote and writeNote|readNote]] IPC, sets state, updates window title.

## Autosave — `saveNote` + `updateContent`

```ts
const saveNote = useCallback((filePath, content) => {
  if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
  saveTimerRef.current = setTimeout(async () => {
    await window.api.writeNote(filePath, content)
  }, 100)
}, [])

const updateContent = useCallback((content) => {
  if (!activeNote) return
  setActiveNote(prev => prev ? { ...prev, content } : null)
  saveNote(activeNote.path, content)
}, [activeNote?.path, saveNote])
```

* `updateContent` updates local state immediately so the [[Editor Component]] stays responsive.
* `saveNote` debounces 100ms — coalesces rapid keystrokes into one write.

Originally 500ms (per the design doc) but tightened to 100ms because users perceived the delay as data loss when closing quickly.

See [[Autosave]] for the broader feature view.

## `createNewNote(name, folderPath?)`

```ts
const createNewNote = useCallback(async (name, folderPath?) => {
  if (!vaultDir || !name.trim()) return undefined
  const targetDir = folderPath ?? vaultDir
  const filePath = await window.api.createNote(targetDir, name.trim())
  await refreshNotes()
  return filePath
}, [vaultDir, refreshNotes])
```

Wraps [[createNote]] IPC. If no folder is given, creates at vault root.

## `deleteCurrentNote()`

```ts
const deleteCurrentNote = useCallback(async () => {
  if (!activeNote) return
  await window.api.deleteNote(activeNote.path)
  setActiveNote(null)
  window.api.setTitle('Noted')
  await refreshNotes()
}, [activeNote, refreshNotes])
```

Only deletes the **active** note. Multi-select deletion bypasses this — see [[Multi-Select Deletion]] / [[App Component]] `handleDeleteItems`.

## `changeVaultDir()`

```ts
const changeVaultDir = useCallback(async () => {
  const newDir = await window.api.selectVaultDir()
  if (newDir) {
    setVaultDir(newDir)
    setActiveNote(null)
    window.api.setTitle('Noted')
  }
}, [])
```

Triggered by clicking the vault label in the sidebar footer. The IPC handler in [[main.ts]] also restarts the [[File Watcher]] and persists the new path to [[Vault Configuration]].

## `renameNote(oldPath, newName)`

```ts
const renameNote = useCallback(async (oldPath, newName) => {
  if (!vaultDir || !newName.trim()) return
  try {
    const result = await window.api.renameNote(vaultDir, oldPath, newName)
    if (activeNote?.path === oldPath) {
      setActiveNote(prev => prev ? { ...prev, path: result.newPath, name: newName } : null)
    }
    await refreshNotes()
    return result
  } catch (error) {
    console.error('Failed to rename note:', error)
    throw error
  }
}, [vaultDir, activeNote?.path, refreshNotes])
```

Wraps [[renameNote]] IPC. If the active note was the one renamed, patch its path/name in place to keep the editor and tab consistent. See [[Rename and References]] for the full feature.

## `createFolder(fullPath)` and `deleteFolder(folderPath)`

Thin wrappers around [[createFolder and deleteFolder|createFolder]] / [[createFolder and deleteFolder|deleteFolder]] IPCs, plus `refreshNotes`. `deleteFolder` additionally clears the active note if it lived inside the deleted folder.

## `moveItem(oldPath, newFolderPath)`

Thin wrapper around [[moveNote]]. See [[Drag and Drop]].

## `resolveLink(linkName)`

```ts
const match = notes.find(n => n.name.toLowerCase() === linkName.toLowerCase())
if (match) {
  await openNote(match.path)
  return match.path
} else {
  const confirmed = await window.api.confirm(`Create new note "${linkName}"?`)
  if (!confirmed) return undefined
  // Use the active note's folder, or vault root
  let targetFolder = vaultDir
  if (activeNote?.path) {
    const sep = activeNote.path.includes('\\') ? '\\' : '/'
    targetFolder = activeNote.path.substring(0, activeNote.path.lastIndexOf(sep))
  }
  const newPath = await createNewNote(linkName, targetFolder)
  if (newPath) await openNote(newPath)
  return newPath
}
```

The wiki-link resolver. **Note:** [[App Component]] **overrides this** with its own version that uses `modal.confirm` from [[useModal]] instead of `window.api.confirm`:

```ts
const { resolveLink: originalResolveLink, … } = useVault()
const resolveLink = useCallback(async (linkName) => {
  // same logic but with modal.confirm
}, [notes, openNote, modal, vaultDir, activeNote?.path, createNewNote])
```

The version exported here is effectively dead code in the current codebase; only [[App Component]]'s override is reached from the [[Wiki Link Plugin]].

## `clearActiveNote()`

Clears `activeNote` and resets the window title. Used by [[App Component]] when the last tab is closed.

## Related

* [[Data Flow]] — Trace 1 (save) and Trace 2 (wiki link click) walk through this hook
* [[Autosave]] — the 100ms debounce
* [[File Watcher]] — produces the events this hook subscribes to
* [[App Component]] — the only consumer
