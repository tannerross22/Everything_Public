# Sidebar Resize and Collapse

The sidebar can be:

* **Resized** by dragging the vertical handle on its right edge.
* **Collapsed** entirely by clicking the hamburger button at the top-left of the title bar.

Both preferences persist across sessions via `localStorage`.

## State

```ts
// in App.tsx
const { width: savedWidth, collapsed: savedCollapsed } = loadSidebarState()
const [sidebarWidth, setSidebarWidth] = useState(savedWidth)        // default 260
const [sidebarCollapsed, setSidebarCollapsed] = useState(savedCollapsed)  // default false
const [isResizing, setIsResizing] = useState(false)
const resizeRef = useRef<{ startX: number; startWidth: number; currentWidth: number } | null>(null)
```

`loadSidebarState` and `saveSidebarState` are from [[localStorage Keys|sidebarStorage]].

## Resize

The resize handle is a thin vertical strip rendered between the sidebar and the content area:

```tsx
{!sidebarCollapsed && (
  <div className="resize-handle" onMouseDown={handleStartResize} title="Drag to resize sidebar" />
)}
```

On mousedown:

```ts
const handleStartResize = (e: React.MouseEvent) => {
  e.preventDefault()
  setIsResizing(true)
  resizeRef.current = { startX: e.clientX, startWidth: sidebarWidth, currentWidth: sidebarWidth }

  const handleResizeMove = (moveEvent: MouseEvent) => {
    if (!resizeRef.current) return
    const delta = moveEvent.clientX - resizeRef.current.startX
    const newWidth = Math.max(180, Math.min(500, resizeRef.current.startWidth + delta))
    resizeRef.current.currentWidth = newWidth
    setSidebarWidth(newWidth)
  }

  const handleResizeEnd = () => {
    setIsResizing(false)
    if (resizeRef.current) saveSidebarState(resizeRef.current.currentWidth, sidebarCollapsed)
    window.removeEventListener('mousemove', handleResizeMove)
    window.removeEventListener('mouseup', handleResizeEnd)
    resizeRef.current = null
  }

  window.addEventListener('mousemove', handleResizeMove)
  window.addEventListener('mouseup', handleResizeEnd)
}
```

* Min width 180, max width 500 pixels.
* The `resizeRef` carries the final width across the closure boundary (state would be stale).
* On `mouseup`, the final width is persisted via `saveSidebarState`.

The `isResizing` flag is applied as the `sidebar-resizing` class on the sidebar so its CSS can disable text selection and `pointer-events` during resize.

## Collapse

The hamburger button in the title bar:

```tsx
<button className="title-rail-btn" onClick={handleToggleSidebarCollapse}>
  <svg>{/* three horizontal lines */}</svg>
</button>
```

```ts
const handleToggleSidebarCollapse = useCallback(() => {
  const newCollapsed = !sidebarCollapsed
  setSidebarCollapsed(newCollapsed)
  saveSidebarState(sidebarWidth, newCollapsed)
}, [sidebarCollapsed, sidebarWidth])
```

When collapsed, the [[Sidebar Component]] is removed from the tree entirely (`!sidebarCollapsed && <Sidebar … />`). The width is remembered so re-expanding restores the previous size.

## What appears when collapsed

The persistent left **rail** (`.app-rail`) — 38px wide, always present. When the sidebar is collapsed and the vault is a git repo, the rail shows the compact sync icon. See [[Custom Title Bar]].

## Persistence

```ts
// src/utils/sidebarStorage.ts
export function loadSidebarState(): SidebarState {
  const widthRaw = localStorage.getItem('noted_sidebar_width')
  const collapsedRaw = localStorage.getItem('noted_sidebar_collapsed')
  return {
    width: widthRaw ? parseInt(widthRaw, 10) : 260,
    collapsed: collapsedRaw ? JSON.parse(collapsedRaw) : false,
  }
}

export function saveSidebarState(width: number, collapsed: boolean): void {
  localStorage.setItem('noted_sidebar_width', String(width))
  localStorage.setItem('noted_sidebar_collapsed', JSON.stringify(collapsed))
}
```

Two localStorage keys, written together. See [[localStorage Keys]].

## Default values

* `width: 260` pixels
* `collapsed: false`

These are baked into `sidebarStorage.ts` and used on first run (or if localStorage is wiped).

## Related

* [[App Component]] — owns the state and handlers
* [[Sidebar Component]] — receives `style={{ width }}` and is conditionally rendered
* [[Custom Title Bar]] — the hamburger button and rail
* [[localStorage Keys]]
