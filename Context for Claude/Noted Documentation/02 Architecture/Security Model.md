# Security Model

Noted enforces Electron's "sandbox + contextBridge" pattern: the renderer cannot touch the operating system except through a whitelist of explicit IPC channels.

## BrowserWindow flags

From [[main.ts]]:

```ts
mainWindow = new BrowserWindow({
  width: 1200,
  height: 800,
  minWidth: 500,
  minHeight: 400,
  frame: false,          // custom title bar — see [[Custom Title Bar]]
  icon: path.join(__dirname, '../electron/app.png'),
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,   // 🔒 renderer can't see preload globals directly
    nodeIntegration: false,   // 🔒 no `require`, no `process`, no Node APIs
    sandbox: true,            // 🔒 OS-level renderer sandbox
  },
})
```

Three layers protect against renderer-side code escaping:

1. **`sandbox: true`** — OS-enforced. The renderer process cannot make syscalls that Chromium hasn't whitelisted. Even if a JS exploit gained arbitrary code execution, it can't directly call `fs.unlinkSync`.

2. **`nodeIntegration: false`** — JS-level. `window.require`, `process`, Node's global objects are not injected. `import fs from 'fs'` would not work in the renderer (and Vite wouldn't even let you try, because `vite-plugin-electron-renderer` is configured for renderer-safe imports only).

3. **`contextIsolation: true`** — V8-level. The preload script and the page script run in separate V8 contexts. The preload's globals are not directly reachable from the page. The only way data crosses is through `contextBridge.exposeInMainWorld('api', …)` in [[preload.ts]], which transfers via structured cloning of plain data.

## The bridge contract

The single point of trust is `window.api`, defined in [[preload.ts]]:

```ts
contextBridge.exposeInMainWorld('api', {
  readNote: (filePath) => ipcRenderer.invoke('vault:read', filePath),
  // …
})
```

The renderer sees `window.api.readNote(path)` and nothing else. There is no way for the renderer to:

* Pick its own IPC channel name.
* Call `ipcRenderer` directly.
* Read or write `fs`.
* Spawn a process.

If a future feature needs renderer-side Node access, the answer is **always**: add a new `ipcMain.handle` in [[main.ts]] and a wrapper in [[preload.ts]]. The renderer cannot, by design, do otherwise.

## Why `confirm()` was replaced

Earlier versions of Noted used the renderer's native `window.confirm()` for delete prompts. This had a nasty side effect on Electron Windows: the confirm dialog corrupted Chromium's focus state, leaving the editor uneditable until the window blurred and refocused. (See [[Noted App Bugs|Bug #10]].)

The fix was to route confirmations through `dialog:confirm` → `dialog.showMessageBox` in the main process — which runs in a separate OS dialog window and doesn't disturb the renderer's focus. This now lives behind `window.api.confirm` in [[preload.ts]] and (newer) `modal.confirm` from [[useModal]] (which shows an in-app React modal instead of a native dialog). The general rule: **never call native `confirm`/`alert`/`prompt` from the renderer**.

## What is **not** locked down

* **`localStorage`.** The renderer freely reads and writes localStorage (used by [[useFolderColors]] and [[sidebarStorage]]). This is fine: localStorage is per-origin and the only "origin" is the local app.
* **`window.open` / external links.** Currently no handling. If a future feature adds external URLs, configure `webContents.setWindowOpenHandler` to `{ action: 'deny' }` and call `shell.openExternal` from main.
* **External git binary.** [[gitSync]] and friends run whatever `git` is on `PATH`. A malicious `git` binary in `PATH` would be trusted by the app. This is the same risk surface as any developer tool.

## Validating IPC input

Currently, [[main.ts]] IPC handlers **trust the renderer's arguments**. For example, `vault:write` writes whatever `filePath` the renderer asks. In our threat model this is acceptable because the renderer is our own React code; an attacker who has injected JS into the renderer has already escaped the sandbox at a higher level.

If Noted ever loaded third-party content (e.g. opened a malicious markdown file with embedded HTML/scripts), we would want to add path validation: `if (!filePath.startsWith(vaultDir)) throw new Error('outside vault')`.

## Related

* [[Process Model]]
* [[IPC Layer]]
* [[preload.ts]]
* [[main.ts]]
* [[Noted App Bugs]] — historical record including Bug #10 (focus trap)
