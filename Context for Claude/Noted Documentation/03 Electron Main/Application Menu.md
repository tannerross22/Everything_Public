# Application Menu

The native OS menu bar Noted attaches via `Menu.setApplicationMenu(menu)`. Built once at window creation in [[main.ts]] inside `setupMenu()`.

## Why a native menu instead of an in-app one?

Two reasons:

1. **Keyboard shortcuts come for free.** Setting `accelerator: 'CmdOrCtrl+N'` on a menu item gives you a system-level shortcut without registering a global hotkey.
2. **OS integration.** The menu shows up in the platform's expected location (top of window on Windows/Linux, top of screen on macOS).

The custom title bar (see [[Custom Title Bar]]) doesn't include menu buttons — it has tabs and window controls instead. The native menu remains available via the platform's standard menu UI.

## Current structure

```
File
├─ New Note              Ctrl+N
├─ Settings              Ctrl+,
├─ ─────────
└─ Sort
    ├─ ● File name (A to Z)
    ├─ ○ File name (Z to A)
    ├─ ○ Modified time (new to old)
    ├─ ○ Modified time (old to new)
    ├─ ○ Created time (new to old)
    └─ ○ Created time (old to new)
```

The sort items use Electron's `type: 'radio'` so only one is checked at a time. (Visually — the menu doesn't know which one the renderer is using; the user has to keep them in sync mentally.)

## How clicks reach the renderer

Each menu item's `click` handler sends an IPC event:

```ts
{
  label: 'New Note',
  accelerator: 'CmdOrCtrl+N',
  click: () => {
    if (mainWindow) mainWindow.webContents.send('menu:newNote')
  },
}
```

Three channels are used:

| Channel | Payload | Subscriber in [[App Component]] |
|---|---|---|
| `menu:newNote` | none | opens the "New Note" prompt modal |
| `menu:openSettings` | none | opens the [[SettingsPage Component]] |
| `menu:setSortOrder` | `SortOrder` string | updates `sortOrder` state |

The renderer subscribes in a `useEffect`:

```ts
const unsubNewNote = window.api.onMenuNewNote(() => {
  setPromptType('note'); setPromptValue(''); setPromptVisible(true)
})
const unsubOpenSettings = window.api.onMenuOpenSettings(() => {
  setShowSettings(true)
})
const unsubSetSortOrder = window.api.onMenuSetSortOrder((order: string) => {
  setSortOrder(order as SortOrder)
})
```

## Known gaps

* **Sort radio doesn't sync.** If the user changes the sort order in some other way (currently they can't — no in-app UI for sort), the native menu's radio dot won't update. To fix this we'd rebuild the menu each time the sort order changes (`Menu.setApplicationMenu(buildMenuWithSelectedSort(sortOrder))`).
* **No "Edit" menu.** Copy/Paste/Undo aren't in the menu — they rely on platform defaults inside the editor. Adding `role: 'editMenu'` would make them appear explicitly.
* **No Help / About.** Future improvement.

## Adding a menu item

To add a new item that the renderer reacts to:

1. Add to the `template` array in `setupMenu()` in [[main.ts]]:
   ```ts
   { label: 'Toggle Graph', accelerator: 'CmdOrCtrl+G', click: () => mainWindow?.webContents.send('menu:toggleGraph') }
   ```
2. Add a subscription helper in [[preload.ts]]:
   ```ts
   onMenuToggleGraph: (cb) => { ipcRenderer.on('menu:toggleGraph', cb); return () => ipcRenderer.removeListener('menu:toggleGraph', cb) }
   ```
3. Type it in [[Types]].
4. Subscribe in [[App Component]]'s menu `useEffect`.

## Related

* [[main.ts]] — `setupMenu()`
* [[Keyboard Shortcuts]] — full shortcut list
* [[App Component]] — the subscriber
