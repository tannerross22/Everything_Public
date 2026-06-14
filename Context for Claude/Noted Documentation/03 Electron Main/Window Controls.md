# Window Controls

Because Noted runs as a frameless window (`frame: false` in [[main.ts]]), it must provide its own minimize / maximize / close buttons and its own drag region. This page documents the **main-process side**; the renderer side is [[Custom Title Bar]].

## The four IPC handlers

Registered in `registerIpcHandlers()` in [[main.ts]]:

```ts
ipcMain.handle('window:minimize', () => mainWindow?.minimize())
ipcMain.handle('window:maximize', () => {
  if (!mainWindow) return
  mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize()
})
ipcMain.handle('window:close', () => mainWindow?.close())
ipcMain.handle('window:isMaximized', () => mainWindow?.isMaximized() ?? false)
```

Plus a fifth for the page title:

```ts
ipcMain.handle('window:setTitle', (_e, title) => mainWindow?.setTitle(title))
```

## What the renderer does with them

In [[App Component]], the title-bar JSX has three buttons in the top right:

```tsx
<button onClick={() => window.api.windowMinimize()}>—</button>
<button onClick={() => { window.api.windowToggleMaximize(); setIsMaximized(m => !m) }}>□</button>
<button onClick={() => window.api.windowClose()}>×</button>
```

The maximize/restore icon swap is driven by local state `isMaximized`, seeded at mount:

```ts
useEffect(() => { window.api.windowIsMaximized().then(setIsMaximized) }, [])
```

The toggle button optimistically flips the state. **Limitation:** if the user maximizes via OS gesture (double-click drag, Win+Up), the state goes out of sync. A fix would be to listen to `mainWindow.on('maximize' | 'unmaximize', …)` and push a new IPC event — not currently implemented.

## `window.setTitle`

Called by [[useVault]] every time the active note changes:

```ts
window.api.setTitle(`Noted - ${name}`)
```

And reset to `'Noted'` when the active note is cleared. The title shows up in the OS taskbar/dock — the in-app title bar doesn't display it.

## The drag region

A frameless window cannot be dragged unless some part of it has the CSS property `-webkit-app-region: drag`. In Noted, **the persistent left rail (`.app-rail`)** is the drag handle. See [[Custom Title Bar]] for why the rail (and not the tab area) ended up with this responsibility.

## Related

* [[Custom Title Bar]] — the renderer-side layout
* [[main.ts]] — handler registrations
* [[App Component]] — where the buttons live in JSX
* [[preload.ts]] — `windowMinimize` / `windowToggleMaximize` / `windowClose` / `windowIsMaximized` / `setTitle`
