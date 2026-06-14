# File Watcher

The Noted file watcher detects external changes to `.md` files in the vault and pushes a `vault:files-changed` event to the renderer.

## Location

Implemented in [[main.ts]]:

```ts
import { watch, type FSWatcher } from 'chokidar'

let fileWatcher: FSWatcher | null = null
let isWriting = false

function startWatcher(vaultDir: string) {
  if (fileWatcher) fileWatcher.close()

  const watchPath = path.join(vaultDir, '**/*.md')
  fileWatcher = watch(watchPath, {
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 300 },
    ignored: ['**/node_modules/**', '**/dist/**', '**/dist-electron/**', '**/.git/**'],
  })

  fileWatcher.on('all', (event, filePath) => {
    if (!isWriting && mainWindow) {
      mainWindow.webContents.send('vault:files-changed')
    }
  })
}
```

## What it watches

* Glob: `${vaultDir}/**/*.md` — recursive, every markdown file.
* Excluded directories: `node_modules`, `dist`, `dist-electron`, `.git`. (Without this, watching a large repo eats CPU + handle quota.)

This complements the **read** exclusion in [[listNotes]] / [[buildFileTree]] (which adds `assets/` too). The watcher exclusions are slightly smaller because chokidar's `ignored` patterns are about filesystem traversal cost, not application logic.

## When it fires

chokidar's `'all'` event fires for `add`, `change`, `unlink`, `addDir`, `unlinkDir`. Each fire ends up calling `mainWindow.webContents.send('vault:files-changed')` (provided `isWriting === false`).

The renderer subscribers — [[useVault]] and [[useGitSync]] — refresh their state on each fire. Multiple chokidar events in rapid succession (e.g. saving 5 files at once) trigger multiple sends; the renderer subscribers debounce on their own side.

## `awaitWriteFinish: { stabilityThreshold: 300 }`

This tells chokidar to wait until a file has been stable for **300ms** before firing a change event. Without it, large saves can trigger multiple `change` events as the file is incrementally flushed. The 300ms is also why the [[useGitSync]] debounce is set to ~400ms (slightly longer, to wait for chokidar to finish reporting).

## The self-write guard (`isWriting`)

When [[main.ts]] performs an internal write (in handlers like `vault:write`, `vault:create`, `vault:delete`, …), it sets `isWriting = true` before the operation and clears it `200–500ms` later. While `isWriting` is true, the `'all'` event handler short-circuits without sending an event.

This avoids an infinite refresh loop: our write triggers a chokidar event, which tells the renderer to refresh, which might trigger another write, etc.

**The post-write `vault:files-changed` event is sent manually** by the handler in [[main.ts]] (after the guard expires), so the renderer still learns about its own write. This decoupling matters because we control the timing — we know the file is fully written, whereas chokidar's event might be early.

Example from `vault:write`:

```ts
ipcMain.handle('vault:write', async (_event, filePath, content) => {
  isWriting = true
  writeNote(filePath, content)
  setTimeout(() => {
    isWriting = false
    mainWindow?.webContents.send('vault:files-changed')
  }, 200)
})
```

The longer guards (500ms for `vault:copyItem`, `vault:deleteFolder`) account for operations that may produce many chokidar events.

## What the renderer does with the event

Two consumers:

### [[useVault]]
```ts
const unsubscribe = window.api.onFilesChanged(() => {
  refreshNotes()
  if (activeNote) {
    window.api.readNote(activeNote.path).then(content => {
      setActiveNote(prev => prev ? { ...prev, content } : null)
    }).catch(() => setActiveNote(null))
  }
})
```

Refreshes the flat list and tree; re-reads the active note's content if it still exists.

### [[useGitSync]]
```ts
let processingTimeout: ReturnType<typeof setTimeout> | null = null

const unsubscribe = window.api.onFilesChanged(async () => {
  if (processingTimeout) clearTimeout(processingTimeout)
  setIsProcessing(true)
  processingTimeout = setTimeout(async () => {
    await refreshGitStatus()
    setIsProcessing(false)
  }, 1000)
})
```

Briefly shows a "processing" indicator on the sync button while waiting for changes to settle, then re-runs `git status` to update the "has changes" badge.

## What it does *not* do

* It does **not** auto-merge external edits with in-memory state. If the user has the editor open on a note and an external editor saves the same file, the [[Editor Component]] does not update to show the external content (Milkdown reads `defaultValueCtx` only at mount). The user has to switch tabs and back. **This is a known gap.**

* It does **not** detect changes to non-`.md` files (the glob is `*.md`). New images dropped into `assets/` won't refresh the sidebar — but since images don't appear in the sidebar tree anyway (the tree is `.md`-only via [[buildFileTree]]), this doesn't matter in practice.

## Bug history

* [[Noted App Bugs|Bug #3]] — original watcher used `path.join(vaultDir, '*.md')` (non-recursive). Fixed to `**/*.md` + ignore list.

## Related

* [[main.ts]] — where `startWatcher` is called
* [[Data Flow]] — Trace 3 walks through an external-edit event
* [[IPC Layer]] — `vault:files-changed` is a main→renderer push channel
* [[useVault]] and [[useGitSync]] — the two consumers
