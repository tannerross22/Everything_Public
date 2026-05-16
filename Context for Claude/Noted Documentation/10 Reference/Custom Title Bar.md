# Custom Title Bar

Noted runs in a **frameless** Electron window (`frame: false`). It draws its own title bar at the top of the window containing the sidebar toggle, tabs, action buttons, and window controls.

## Why

Three reasons:

1. **Theme consistency.** The native title bar (white on Windows) doesn't match the app's dark theme.
2. **More vertical space.** Combining tabs with window chrome saves ~30px.
3. **Custom controls.** Lets us add the `+`, search, graph buttons next to min/max/close.

## Layout

```
.app  (flex column, 100vh)
│
├── .title-bar  (38px tall)
│   ├── .title-rail-btn   (38px wide — hamburger; toggles sidebar)
│   ├── .title-tabs       (flex:1 — [[TabBar Component]] inside)
│   └── .title-controls   (right side — +, search, graph, min, max, close)
│
└── .body-row  (flex row, flex:1)
    ├── .app-rail   (38px wide — persistent left strip; sync icon when sidebar collapsed)
    └── .body-content
        ├── [[Sidebar Component]]  (when not collapsed)
        ├── .resize-handle
        └── .content   ([[Editor Component]] or [[GraphView Component]])
```

## The drag region

A frameless window can only be moved by the user if some part of it has `-webkit-app-region: drag`. Naively making the whole title bar draggable would block clicks on the tabs and buttons inside it.

The actual configuration is:

```css
.title-bar           { -webkit-app-region: drag; }         /* base: draggable */
.title-rail-btn      { -webkit-app-region: no-drag; }      /* the hamburger button */
.title-tabs          { -webkit-app-region: drag; }         /* gaps in tab area still draggable... */
.title-tabs .tab-bar { -webkit-app-region: no-drag; }      /* but the tab strip itself is not */
.title-tabs .tabs-container { -webkit-app-region: no-drag; }
.title-tabs .tab     { -webkit-app-region: no-drag; }      /* tabs interactive */
.title-controls      { -webkit-app-region: no-drag; }      /* right-side buttons */
.app-rail            { -webkit-app-region: drag;            /* primary drag handle */
                       user-select: none; }
.rail-sync-btn       { -webkit-app-region: no-drag; }      /* but the sync button is interactive */
```

The **left rail** (`.app-rail`) is the primary drag handle. This was an iterative discovery — earlier versions tried to make the tab-bar gaps draggable, but that broke scroll wheel events (the drag region intercepted them). The current layout sacrifices some tab-area drag space to keep scrolling and clicking reliable. See [[TabBar Component]] for the scroll vs. drag conflict history.

## The hamburger button

```tsx
<button className="title-rail-btn" onClick={handleToggleSidebarCollapse} title={…}>
  <svg width="16" height="16" viewBox="0 0 16 16">
    <rect x="1" y="3"     width="14" height="1.5" rx="0.75" fill="currentColor"/>
    <rect x="1" y="7.25"  width="14" height="1.5" rx="0.75" fill="currentColor"/>
    <rect x="1" y="11.5"  width="14" height="1.5" rx="0.75" fill="currentColor"/>
  </svg>
</button>
```

Three horizontal lines. Toggles `sidebarCollapsed` in [[App Component]]. See [[Sidebar Resize and Collapse]].

## The action buttons

The right side of the title bar has three "action" buttons + a separator + three window control buttons:

```tsx
<div className="title-controls">
  <button className="title-action-btn" onClick={createNoteInNewTab}>+</button>
  <button className="title-action-btn" onClick={() => setSearchVisible(true)}>{/* magnifying glass */}</button>
  <button className={`title-action-btn ${viewMode === 'graph' ? 'active' : ''}`} onClick={() => setViewMode(v => v === 'graph' ? 'editor' : 'graph')}>{/* graph icon */}</button>
  <div className="win-ctrl-sep" />
  <button className="win-ctrl" onClick={() => window.api.windowMinimize()}>{/* minus */}</button>
  <button className="win-ctrl" onClick={() => { window.api.windowToggleMaximize(); setIsMaximized(m => !m) }}>{/* square or restore */}</button>
  <button className="win-ctrl win-ctrl-close" onClick={() => window.api.windowClose()}>{/* x */}</button>
</div>
```

* **+** opens the New Note prompt (same as Ctrl+N or menu).
* **Search** opens [[SearchBar Component]].
* **Graph** toggles `viewMode`.
* **Min / Max / Close** route to [[Window Controls]] IPC.

The close button gets a red background on hover (`.win-ctrl-close:hover { background: #e81123; color: #fff }`) matching Windows' native red close.

## Tracking the maximized state

```ts
const [isMaximized, setIsMaximized] = useState(false)

useEffect(() => {
  window.api.windowIsMaximized().then(setIsMaximized)
}, [])
```

Polled once at mount. The icon swaps (filled square for maximize, restore icon when maximized). Clicking the button optimistically flips the state. **Caveat:** if the user maximizes via OS gesture (Win+Up, drag to top, double-click drag), state goes out of sync. A fix would be to listen to Electron's `maximize`/`unmaximize` events on `mainWindow` and push back via IPC. Not implemented.

## The persistent rail

`.app-rail` is a 38px-wide vertical strip that's **always present**, even when the sidebar is collapsed. It serves two purposes:

1. **Window drag handle.** As described above, this is the primary drag region.
2. **Compact sync icon.** When `sidebarCollapsed && isRepo`, the small `.rail-sync-btn` appears here.

```tsx
<div className="app-rail">
  {gitSync.isRepo && (
    <button className={`rail-sync-btn ${stateClasses}`}
            onClick={gitSync.handleSync}
            disabled={…} title={…} />
  )}
</div>
```

The button is a circle indicator — yellow when changes exist, spinning when syncing/processing, flash on success. See [[Git Sync]] for visual states.

## Tab overflow

The `.title-tabs .tabs-container` is `overflow-x: auto` with a hidden scrollbar. Each tab is `flex-shrink: 0; min-width: 80px; max-width: 160px`, so many open tabs push the strip into horizontal scroll instead of squishing each tab. See [[TabBar Component]].

## Related

* [[Window Controls]] — the main-process IPC for min/max/close
* [[TabBar Component]] — the tab strip
* [[Sidebar Resize and Collapse]] — the hamburger toggle target
* [[Git Sync]] — the rail sync icon
* [[App Component]] — owns the title-bar JSX
