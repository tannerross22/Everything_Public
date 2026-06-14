# IPC Channels

Every IPC channel registered by [[main.ts]] and exposed via [[preload.ts]]. Use this as a quick reference; the architecture is in [[IPC Layer]].

## `vault:*` — Vault and filesystem

| Channel | preload method | Args → Returns | Doc |
|---|---|---|---|
| `vault:getDir` | `getVaultDir()` | () → `string` | [[Vault Configuration]] |
| `vault:selectDir` | `selectVaultDir()` | () → `string \| null` | [[Vault Configuration]] |
| `vault:list` | `listNotes(vaultDir)` | `(vaultDir)` → `NoteFileData[]` | [[listNotes]] |
| `vault:tree` | `buildFileTree(vaultDir)` | `(vaultDir)` → `FileTreeNode[]` | [[buildFileTree]] |
| `vault:read` | `readNote(filePath)` | `(filePath)` → `string` | [[readNote and writeNote]] |
| `vault:write` | `writeNote(filePath, content)` | `(filePath, content)` → `void` | [[readNote and writeNote]] |
| `vault:create` | `createNote(vaultDir, name)` | `(vaultDir, name)` → `string` (new path) | [[createNote]] |
| `vault:delete` | `deleteNote(filePath)` | `(filePath)` → `void` | [[deleteNote]] |
| `vault:createFolder` | `createFolder(folderPath)` | `(folderPath)` → `string` | [[createFolder and deleteFolder]] |
| `vault:deleteFolder` | `deleteFolder(folderPath)` | `(folderPath)` → `void` | [[createFolder and deleteFolder]] |
| `vault:moveNote` | `moveNote(oldPath, newFolderPath)` | `(oldPath, newFolderPath)` → `string` (new path) | [[moveNote]] |
| `vault:copyItem` | `copyItem(sourcePath, destFolder)` | `(sourcePath, destFolder)` → `string` (new path) | [[copyItem]] |
| `vault:rename` | `renameNote(vaultDir, oldPath, newName)` | `(vaultDir, oldPath, newName)` → `{newPath, updatedCount}` | [[renameNote]] |
| `vault:saveImage` | `saveImage(vaultDir, arrayBuffer, type)` | `(vaultDir, arrayBuffer, type)` → `string` (relative path) | [[Image Pipeline]] |
| `vault:convertBase64ImagesToFiles` | `convertBase64ImagesToFiles(vaultDir, noteId, markdown)` | → `string` (updated markdown) | [[Image Pipeline]] |

## `git:*` — Git operations

| Channel | preload methods | Args → Returns | Doc |
|---|---|---|---|
| `git:isRepo` | `isGitRepo(v)` / `gitIsRepo(v)` | `(v)` → `boolean` | [[isGitRepo]] |
| `git:status` | `gitStatus(v)` | `(v)` → `string` (porcelain) | [[gitStatus]] |
| `git:sync` | `gitSync(v, message)` | `(v, message)` → `string` | [[gitSync]] |
| `git:log` | `gitLog(v, count)` | `(v, count)` → `string` | [[gitLog]] |
| `git:init` | `gitInit(v)` | `(v)` → `string` | [[gitInit]] |
| `git:addRemote` | `gitAddRemote(v, name, url)` | `(v, name, url)` → `string` | [[gitAddRemote]] |
| `git:getRemoteUrl` | `gitGetRemoteUrl(v, name?)` | `(v, name='origin')` → `string` | [[gitGetRemoteUrl]] |
| `git:initialCommit` | `gitInitialCommit(v, message)` | `(v, message)` → `string` | [[gitInitialCommit]] |

## `window:*` — Window controls

| Channel | preload method | Args → Returns | Doc |
|---|---|---|---|
| `window:minimize` | `windowMinimize()` | () → `void` | [[Window Controls]] |
| `window:maximize` | `windowToggleMaximize()` | () → `void` | [[Window Controls]] |
| `window:close` | `windowClose()` | () → `void` | [[Window Controls]] |
| `window:isMaximized` | `windowIsMaximized()` | () → `boolean` | [[Window Controls]] |
| `window:setTitle` | `setTitle(title)` | `(title)` → `void` | [[Window Controls]] |

## `dialog:*` — Native dialogs

| Channel | preload method | Args → Returns | Notes |
|---|---|---|---|
| `dialog:confirm` | `confirm(message)` | `(message)` → `boolean` | Uses `dialog.showMessageBox`. Prefer [[useModal]] for new code. |

## One-way main → renderer events

These use `mainWindow.webContents.send(channel, …)` from main and `ipcRenderer.on(channel, cb)` from the renderer (wrapped in preload helpers that return cleanup functions).

| Channel | preload subscriber | Payload | Sender | Subscriber |
|---|---|---|---|---|
| `vault:files-changed` | `onFilesChanged(cb)` | none | [[File Watcher]] + every mutating IPC handler + post-[[gitSync]] | [[useVault]], [[useGitSync]] |
| `menu:newNote` | `onMenuNewNote(cb)` | none | [[Application Menu]] "New Note" | [[App Component]] |
| `menu:openSettings` | `onMenuOpenSettings(cb)` | none | [[Application Menu]] "Settings" | [[App Component]] |
| `menu:setSortOrder` | `onMenuSetSortOrder(cb)` | `string` | [[Application Menu]] Sort submenu | [[App Component]] |

Each subscriber method returns a cleanup function that removes the listener — typically invoked in a `useEffect` cleanup.

## Adding a new channel

1. Add `ipcMain.handle('your:channel', (_e, …args) => …)` in [[main.ts]].
2. Add the preload wrapper in [[preload.ts]]: `yourChannel: (…args) => ipcRenderer.invoke('your:channel', …args)`.
3. Add the TypeScript signature to `src/global.d.ts` ([[Types]]).
4. Call `window.api.yourChannel(...)` from the renderer.

## Related

* [[IPC Layer]] — architecture and idioms
* [[main.ts]] — handler registrations
* [[preload.ts]] — bridge surface
* [[Types]] — type declarations
