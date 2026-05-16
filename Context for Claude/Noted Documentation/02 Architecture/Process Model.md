# Process Model

Noted runs in **two cooperating processes** plus an **external git subprocess**.

## The two processes

### Electron Main (Node.js)
* Single process per running app.
* Has full Node.js access: `fs`, `path`, `child_process`, `os`, `electron` APIs (`app`, `BrowserWindow`, `dialog`, `Menu`, `ipcMain`).
* Owns: the window, the [[File Watcher]], the application menu, vault config persistence, all filesystem and git work.
* Entry point: [[main.ts]].
* Source: `electron/main.ts`, `electron/fileService.ts`.

### Renderer (Chromium)
* Lives inside `BrowserWindow.webContents`. One per window — Noted only ever has one window.
* **Sandboxed**: `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`. No `fs`, no `require`, no Node anything. See [[Security Model]].
* Renders the React UI: [[App Component]] mounts in `src/main.tsx`.
* Communicates with the main process **only** via `window.api`, exposed by [[preload.ts]].

```
┌────────────────────── Electron Main (Node) ──────────────────────┐
│                                                                  │
│   BrowserWindow      ipcMain handlers       chokidar watcher     │
│        │                  │                       │              │
│        │                  ▼                       │              │
│        │            fileService.ts ───── execFile('git', …) ─▶   │
│        │                                                         │
└────────┼─────────────────────────────────────────────────────────┘
         │                                ▲           ▲
   loads │                                │ IPC       │ event
         ▼                                │           │ ('vault:files-changed')
┌──────────────── Renderer (Chromium, sandboxed) ───────────────────┐
│                                                                   │
│   preload.ts ──── window.api ◀── ipcRenderer.invoke / on ─────────┤
│                       ▲                                           │
│                       │ called from                               │
│   App.tsx → useVault, useGitSync, useGraph                        │
│              │                                                    │
│              └──▶ Sidebar / Editor / GraphView / …                │
└───────────────────────────────────────────────────────────────────┘
```

## Why two processes?

1. **Security.** A renderer process can be tricked into running arbitrary JS (e.g. via a malicious markdown extension someday). Keeping `fs`/`exec` out of the renderer means an exploit cannot exfiltrate or destroy files without an IPC handler that explicitly permits the operation. See [[Security Model]].

2. **Single source of truth for OS state.** Only one process owns the file watcher. The renderer subscribes to its events rather than running its own watcher in parallel.

3. **API isolation.** The IPC surface (defined in [[preload.ts]]) is the only contract between UI and OS. Every renderer-side feature you build must add or reuse an `ipcMain.handle` channel in [[main.ts]].

## What lives where

| Concern | Process | File(s) |
|---|---|---|
| BrowserWindow setup | Main | [[main.ts]] |
| Vault config (`noted-config.json`) | Main | [[main.ts]] (`loadConfig`/`saveConfig`) |
| File reads/writes | Main | [[fileService.ts]] |
| Git CLI invocations | Main | [[fileService.ts]] |
| chokidar | Main | [[main.ts]] (`startWatcher`) |
| Application menu | Main | [[main.ts]] (`setupMenu`) |
| Window controls (min/max/close) | Main | [[main.ts]] IPC handlers |
| Confirm dialog | Main (via `dialog.showMessageBox`) | [[main.ts]] |
| All UI | Renderer | `src/**/*` |
| Wiki link decorations | Renderer | [[Wiki Link Plugin]] |
| Graph simulation | Renderer | [[GraphView Component]] |
| Autosave debounce | Renderer | [[useVault]] |

## Lifecycle

```
app.whenReady()  ──▶  registerIpcHandlers()  ──▶  createWindow()
                                                       │
                                                       ▼
                                          new BrowserWindow({ frame: false, … })
                                                       │
                                                       ▼
                                          loadURL(VITE_DEV_SERVER_URL) or loadFile(dist/index.html)
                                                       │
                                                       ▼
                                          startWatcher(vaultDir)
                                                       │
                                                       ▼
                                          setupMenu()    ◀── menu items send IPC ('menu:newNote', …)
```

On the renderer side, `src/main.tsx` calls `ReactDOM.createRoot(…).render(<App />)`. [[App Component]] then orchestrates everything.

## Event flow back from main to renderer

The main process sends to the renderer with `mainWindow.webContents.send(channel, …)`. Two channels are used:

* `vault:files-changed` — fired by [[File Watcher]] (or after a write) so the renderer can refresh. Subscribed via `window.api.onFilesChanged` in [[useVault]] and [[useGitSync]].
* `menu:newNote`, `menu:openSettings`, `menu:setSortOrder` — fired by [[Application Menu]] items. Subscribed in [[App Component]].

## Related

* [[IPC Layer]] — every channel, what it does
* [[Security Model]] — why sandboxing matters
* [[Data Flow]] — concrete trace of how a keystroke reaches the disk
* [[main.ts]] — the main-process entry file
