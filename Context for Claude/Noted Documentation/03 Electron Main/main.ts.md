# main.ts

**Path:** `electron/main.ts`

The Electron main-process entry point. Owns the window, the [[File Watcher]], the [[Application Menu]], the [[Vault Configuration]] file, and every `ipcMain.handle` for the [[IPC Layer]].

## Module-level state

```ts
let mainWindow: BrowserWindow | null = null
let fileWatcher: FSWatcher | null = null
let isWriting = false   // suppress watcher events during our own writes
const configPath = path.join(app.getPath('userData'), 'noted-config.json')
```

* `mainWindow` — the one and only BrowserWindow. Re-created on macOS `activate` if all windows closed.
* `fileWatcher` — the chokidar instance. Closed and recreated when the vault changes.
* `isWriting` — the **self-write guard**. See [[IPC Layer]] for why this exists.
* `configPath` — `%APPDATA%/Noted/noted-config.json` on Windows.

## `loadConfig()` / `saveConfig()`

Persist the vault directory across launches.

```ts
function loadConfig(): { vaultDir: string }
function saveConfig(config: { vaultDir: string })
```

* If the config file is missing or unparseable, returns `{ vaultDir: path.resolve(__dirname, '..', '..') }` — i.e. two levels above `dist-electron/`, which is the repo root (`Everything_Public`). See [[Vault Configuration]].
* `saveConfig` writes JSON pretty-printed.

## `startWatcher(vaultDir)`

See [[File Watcher]] for the deep dive. Briefly:

* Closes any existing `fileWatcher`.
* Creates a new chokidar watch on `path.join(vaultDir, '**/*.md')`.
* On any change/add/delete event, sends `vault:files-changed` to the renderer **unless** `isWriting` is currently true.

## `createWindow()`

```ts
mainWindow = new BrowserWindow({
  width: 1200, height: 800,
  minWidth: 500, minHeight: 400,
  frame: false,                // [[Custom Title Bar]]
  icon: 'electron/app.png',
  webPreferences: {
    preload: 'preload.js',
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,             // [[Security Model]]
  },
})
```

In dev mode (`VITE_DEV_SERVER_URL` is set by `vite-plugin-electron`), it `loadURL`s that. In production it `loadFile`s `../dist/index.html`. After load, it starts the [[File Watcher]] and the [[Application Menu]].

## `setupMenu()`

Builds the application menu. Currently a single "File" menu with three items: New Note (Ctrl+N), Settings (Ctrl+,), Sort (with submenu of [[Keyboard Shortcuts|six sort orders]]). Clicking any item sends an IPC event to the renderer:

* `menu:newNote`
* `menu:openSettings`
* `menu:setSortOrder` (with the order string as payload)

Subscribers are in [[App Component]].

## `registerIpcHandlers()`

Registers **every** main-process IPC handler. Grouped by concern:

### Vault directory
* `vault:getDir` → `loadConfig().vaultDir`
* `vault:selectDir` → `dialog.showOpenDialog(…)` + `saveConfig` + restart watcher

### File operations (write-class guards `isWriting`)
* `vault:list` → [[listNotes]]
* `vault:tree` → [[buildFileTree]]
* `vault:createFolder` → [[createFolder]]
* `vault:moveNote` → [[moveNote]]
* `vault:copyItem` → [[copyItem]] (guarded)
* `vault:read` → [[readNote]]
* `vault:write` → [[writeNote]] (guarded, emits `vault:files-changed` 200ms later)
* `vault:create` → [[createNote]] (guarded)
* `vault:delete` → [[deleteNote]] (guarded)
* `vault:deleteFolder` → [[deleteFolder]] (guarded, 500ms)
* `vault:rename` → [[renameNote]] (guarded)

### Git operations
* `git:isRepo` → [[isGitRepo]]
* `git:status` → [[gitStatus]]
* `git:sync` → [[gitSync]] (also emits `vault:files-changed` after success)
* `git:log` → [[gitLog]]
* `git:init` → [[gitInit]]
* `git:addRemote` → [[gitAddRemote]]
* `git:getRemoteUrl` → [[gitGetRemoteUrl]]
* `git:initialCommit` → [[gitInitialCommit]]

### [[Window Controls]]
* `window:minimize` → `mainWindow?.minimize()`
* `window:maximize` → toggles between `maximize` and `unmaximize`
* `window:close` → `mainWindow?.close()`
* `window:isMaximized` → boolean
* `window:setTitle` → `mainWindow.setTitle(title)`

### Dialogs
* `dialog:confirm` → `dialog.showMessageBox` (used for the legacy native confirm; see [[Modal Component]] and [[useModal]] for the React-side replacement)

### Image handling
* `vault:saveImage` → [[saveImage]] (after `Buffer.from(arrayBuffer)`)
* `vault:convertBase64ImagesToFiles` → [[convertBase64ImagesToFiles]]

## App lifecycle

```ts
app.whenReady().then(() => {
  registerIpcHandlers()
  createWindow()
})

app.on('window-all-closed', () => {
  if (fileWatcher) fileWatcher.close()
  app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
```

* On Windows/Linux, closing the last window quits the app. The watcher is explicitly closed first to avoid lingering inotify/ReadDirectoryChangesW handles.
* On macOS, the app stays open with no windows; clicking the dock icon recreates one.

## Where each behavior is documented

| Concern | Doc |
|---|---|
| Watcher | [[File Watcher]] |
| Menu | [[Application Menu]] |
| Window chrome (min/max/close) | [[Window Controls]] |
| Frameless drag | [[Custom Title Bar]] |
| Config file | [[Vault Configuration]] |
| File IO | [[fileService.ts]] |
| Git CLI | [[Git Overview]] |

## Related

* [[preload.ts]] — the bridge it talks to
* [[fileService.ts]] — what each IPC handler actually invokes
* [[Process Model]]
* [[IPC Channels]] — index of every channel
