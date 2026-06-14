# IPC Layer

Everything the renderer can ask the main process to do happens through Electron IPC. This page explains the architecture; the full list of channels is in [[IPC Channels]].

## Three building blocks

| Concept | Where | What |
|---|---|---|
| `ipcMain.handle(channel, fn)` | [[main.ts]] | Registers a Promise-returning handler. |
| `ipcRenderer.invoke(channel, …args)` | [[preload.ts]] | Renderer calls handler, awaits Promise. |
| `mainWindow.webContents.send(channel, …)` + `ipcRenderer.on(channel, cb)` | [[main.ts]] / [[preload.ts]] | One-way push from main to renderer (e.g. file-change events, menu commands). |

The renderer **never sees** `ipcRenderer` directly — it sees only the methods on `window.api`, surfaced by `contextBridge.exposeInMainWorld('api', …)` in [[preload.ts]]. This is the [[Security Model]] guarantee.

## End-to-end shape of one IPC round trip

Example: opening a note when the user clicks it in the sidebar.

```
[Sidebar.tsx]
  onClick → onOpenNote(node.path)
        │
        ▼
[App.tsx]  openNoteInTab(path)
        │  calls openNote from useVault
        ▼
[useVault.ts]  await window.api.readNote(filePath)
        │
        ▼
[preload.ts]  readNote(filePath) → ipcRenderer.invoke('vault:read', filePath)
        │            ─────── crosses process boundary ───────
        ▼
[main.ts]  ipcMain.handle('vault:read', (_e, filePath) => readNote(filePath))
        │
        ▼
[fileService.ts]  fs.readFileSync(filePath, 'utf-8')
        │
        ▲  returns string content (resolved Promise)
        │
[useVault.ts]  setActiveNote({ name, path, content })
        │
        ▼
[Editor.tsx]  receives new content prop, re-mounts via key={path}
```

Every other operation follows the same pattern. The full surface is in [[IPC Channels]].

## Channel naming convention

| Prefix | Concern |
|---|---|
| `vault:*` | File system, vault directory, tree, notes, folders |
| `git:*` | Git operations |
| `window:*` | Window controls (min/max/close/title) |
| `dialog:*` | Native dialogs (currently just confirm) |
| `menu:*` | Main → renderer **events** triggered by Application Menu clicks |

## Categories of channels

### Bidirectional (invoke / handle)
The renderer calls; the main process returns a value (or void).

* All [[File Operations]]: `vault:list`, `vault:tree`, `vault:read`, `vault:write`, `vault:create`, `vault:delete`, `vault:deleteFolder`, `vault:createFolder`, `vault:moveNote`, `vault:copyItem`, `vault:rename`.
* All [[Git Operations]]: `git:isRepo`, `git:status`, `git:sync`, `git:log`, `git:init`, `git:addRemote`, `git:getRemoteUrl`, `git:initialCommit`.
* Vault config: `vault:getDir`, `vault:selectDir`.
* Window: `window:minimize`, `window:maximize`, `window:close`, `window:isMaximized`, `window:setTitle`.
* Dialogs: `dialog:confirm`.
* Image pipeline: `vault:saveImage`, `vault:convertBase64ImagesToFiles`.

### One-way push (main → renderer)
The main process pushes; the renderer subscribes via a callback.

* `vault:files-changed` — file watcher detected an external (or post-write) change. Subscribers: [[useVault]] and [[useGitSync]].
* `menu:newNote`, `menu:openSettings`, `menu:setSortOrder` — fired by [[Application Menu]] items. Subscriber: [[App Component]].

## The self-write guard

When the renderer asks main to **write** a file (`vault:write`, `vault:create`, etc.), main turns on a flag `isWriting = true` for ~200–500ms. While this flag is on, the [[File Watcher]] suppresses `vault:files-changed` events. This prevents an infinite loop where our own write would re-trigger a refresh.

The guard is per-operation, set in every mutating IPC handler in [[main.ts]] (`vault:write`, `vault:create`, `vault:delete`, `vault:deleteFolder`, `vault:rename`, `vault:copyItem`).

## Typing the bridge

The shape of `window.api` is declared in `src/global.d.ts` ([[Types]]). Every time a new channel is added, three places must be touched:

1. `electron/main.ts` — `ipcMain.handle('new:channel', …)`
2. `electron/preload.ts` — `newChannelMethod: (…args) => ipcRenderer.invoke('new:channel', …args)`
3. `src/global.d.ts` — `newChannelMethod: (…) => Promise<…>`

## Related

* [[IPC Channels]] — exhaustive list with signatures
* [[preload.ts]] — the actual bridge implementation
* [[main.ts]] — handler registrations
* [[Types]] — `window.api` type definitions
* [[Security Model]] — why this indirection exists
