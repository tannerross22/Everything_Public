# preload.ts

**Path:** `electron/preload.ts`

The Electron preload script. Runs **before** the renderer's React code in a privileged V8 context, and uses `contextBridge` to expose a single object — `window.api` — that is the renderer's **only** access to the operating system.

## How it gets loaded

In [[main.ts]]:

```ts
new BrowserWindow({
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),   // built from preload.ts
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
  },
})
```

Vite compiles `electron/preload.ts` to `dist-electron/preload.js`. See [[Build and Config]].

## The contextBridge call

```ts
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('api', {
  // …methods that wrap ipcRenderer.invoke / on…
})
```

`contextBridge.exposeInMainWorld('api', obj)` does two things:

1. Adds a property `window.api` to the renderer's V8 context.
2. **Deep-clones** `obj` across the V8 boundary. This means functions are wrapped — when the renderer calls `window.api.readNote(p)`, the wrapper forwards the call back to the preload-side function.

This is the only escape hatch from the [[Security Model]]'s `contextIsolation: true`.

## The exposed surface (categorized)

For the complete signatures, see [[IPC Channels]] and [[Types]].

### Vault directory
| Method | IPC channel | Returns |
|---|---|---|
| `getVaultDir()` | `vault:getDir` | `Promise<string>` |
| `selectVaultDir()` | `vault:selectDir` | `Promise<string \| null>` |

### File operations
| Method | IPC channel | File service fn |
|---|---|---|
| `listNotes(vaultDir)` | `vault:list` | [[listNotes]] |
| `buildFileTree(vaultDir)` | `vault:tree` | [[buildFileTree]] |
| `readNote(filePath)` | `vault:read` | [[readNote]] |
| `writeNote(filePath, content)` | `vault:write` | [[writeNote]] |
| `createNote(vaultDir, name)` | `vault:create` | [[createNote]] |
| `deleteNote(filePath)` | `vault:delete` | [[deleteNote]] |
| `deleteFolder(folderPath)` | `vault:deleteFolder` | [[deleteFolder]] |
| `renameNote(vaultDir, oldPath, newName)` | `vault:rename` | [[renameNote]] |
| `createFolder(folderPath)` | `vault:createFolder` | [[createFolder]] |
| `moveNote(oldPath, newFolderPath)` | `vault:moveNote` | [[moveNote]] |
| `copyItem(sourcePath, destFolder)` | `vault:copyItem` | [[copyItem]] |

### Subscriptions (one-way main→renderer)
Each subscription method registers an `ipcRenderer.on` listener and **returns a cleanup function**. Callers must invoke the returned function (typically in a `useEffect` cleanup) to remove the listener.

```ts
onFilesChanged: (callback: () => void) => {
  ipcRenderer.on('vault:files-changed', callback)
  return () => ipcRenderer.removeListener('vault:files-changed', callback)
}
```

| Method | IPC channel | Subscribers |
|---|---|---|
| `onFilesChanged(cb)` | `vault:files-changed` | [[useVault]], [[useGitSync]] |
| `onMenuNewNote(cb)` | `menu:newNote` | [[App Component]] |
| `onMenuOpenSettings(cb)` | `menu:openSettings` | [[App Component]] |
| `onMenuSetSortOrder(cb)` | `menu:setSortOrder` | [[App Component]] |

### Git operations
| Method | IPC channel | File service fn |
|---|---|---|
| `isGitRepo(v)` / `gitIsRepo(v)` | `git:isRepo` | [[isGitRepo]] |
| `gitStatus(v)` | `git:status` | [[gitStatus]] |
| `gitSync(v, message)` | `git:sync` | [[gitSync]] |
| `gitLog(v, count)` | `git:log` | [[gitLog]] |
| `gitInit(v)` | `git:init` | [[gitInit]] |
| `gitAddRemote(v, name, url)` | `git:addRemote` | [[gitAddRemote]] |
| `gitGetRemoteUrl(v, name?)` | `git:getRemoteUrl` | [[gitGetRemoteUrl]] |
| `gitInitialCommit(v, msg)` | `git:initialCommit` | [[gitInitialCommit]] |

> `gitIsRepo` is an alias for `isGitRepo` — both names exist because callsites accumulated organically.

### [[Window Controls]] (frameless window)
| Method | IPC channel |
|---|---|
| `setTitle(title)` | `window:setTitle` |
| `windowMinimize()` | `window:minimize` |
| `windowToggleMaximize()` | `window:maximize` |
| `windowClose()` | `window:close` |
| `windowIsMaximized()` | `window:isMaximized` |

### Native dialog
| Method | IPC channel |
|---|---|
| `confirm(message)` | `dialog:confirm` |

Use [[useModal]] for any new code — `window.api.confirm` exists for legacy reasons (see [[Security Model]] for context on focus-trap).

### Image handling
| Method | IPC channel | File service fn |
|---|---|---|
| `saveImage(vaultDir, arrayBuffer, type)` | `vault:saveImage` | [[saveImage]] |
| `convertBase64ImagesToFiles(vault, id, md)` | `vault:convertBase64ImagesToFiles` | [[convertBase64ImagesToFiles]] |

## Adding a new channel

Three places to edit, in this order:

1. **Handler:** `ipcMain.handle('new:channel', (_e, …args) => …)` in [[main.ts]].
2. **Bridge:** `newChannel: (…args) => ipcRenderer.invoke('new:channel', …args)` here in `preload.ts`.
3. **Type:** add to `Window.api` in `src/global.d.ts` ([[Types]]).

Forgetting step 3 results in TypeScript errors at every callsite, which is the safety net that has prevented several bugs.

## Related

* [[main.ts]] — what answers each invoke
* [[IPC Channels]] — exhaustive table
* [[Types]] — the declaration file
* [[Security Model]] — why this bridge is the entire OS access surface
