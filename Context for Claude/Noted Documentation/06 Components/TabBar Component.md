# TabBar Component

**Path:** `src/components/TabBar.tsx`

Renders the row of open-note tabs in the title bar. Each tab shows the note name and an `×` close button.

## Props

```ts
interface TabBarProps {
  tabs: OpenTab[]
  activeIndex: number
  onTabClick: (index: number) => void
  onTabClose: (index: number) => void
  // For context menu only
  onNewNote: () => void
  onNewFolder: () => void
  clipboardPath: string | null
  onPaste: () => void
}

export interface OpenTab {
  path: string
  name: string
}
```

The `tabs` array and selection state live in [[App Component]] — TabBar is a presentational/event component.

## Local state

```ts
const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number } | null>(null)
```

Only used for the right-click context menu (New Note / New Folder / Paste).

## Render

```tsx
<div className="tab-bar" onContextMenu={handleContextMenu} onClick={closeCtx}>
  <div className="tabs-container">
    {tabs.map((tab, i) => (
      <div className={`tab ${i === activeIndex ? 'active' : ''}`}
           onClick={() => onTabClick(i)}>
        <span className="tab-name">{tab.name}</span>
        <button className="tab-close" onClick={e => { e.stopPropagation(); onTabClose(i) }}>×</button>
      </div>
    ))}
  </div>
  {ctxMenu && <ContextMenu />}
</div>
```

## The drag/scroll conflict (and its resolution)

The TabBar sits inside `.title-tabs`, which inside `.title-bar`. The title bar has `-webkit-app-region: drag` so the user can drag the window. But `drag` regions consume **all** pointer events — including scroll wheel and clicks.

This created two bugs during development:

1. **Tab close × buttons stopped working** — clicks were intercepted by the drag region.
2. **Tab scroll only worked one direction** — wheel events were partially intercepted.

The fix layered `-webkit-app-region: no-drag` carefully:

```css
.title-tabs           { -webkit-app-region: drag; }      /* gaps still draggable */
.title-tabs .tab-bar  { -webkit-app-region: no-drag; }   /* tabs interactive */
.title-tabs .tabs-container { -webkit-app-region: no-drag; }
.title-tabs .tab      { -webkit-app-region: no-drag; }
```

The result: tabs are fully interactive, but **only tabs** — there's no draggable gap inside the tab area. The window drag region was relocated to the [[Custom Title Bar|persistent left rail]] (`.app-rail`).

## Scrollable overflow

Many open tabs would push the close button out of the title bar. The container is set to `overflow-x: auto` with a hidden scrollbar:

```css
.title-tabs .tabs-container {
  overflow-x: auto;
  scrollbar-width: none;
}
.title-tabs .tabs-container::-webkit-scrollbar { display: none; }
.title-tabs .tab { flex-shrink: 0; min-width: 80px; max-width: 160px; }
```

`flex-shrink: 0` on the tab means each one keeps its width; `overflow-x: auto` on the container makes the strip scroll. Mouse wheel scroll works horizontally when hovering tabs (Chromium maps vertical wheel → horizontal scroll when there's no vertical overflow).

## Right-click context menu

Right-clicking **anywhere in the tab bar** (but not on a specific tab — that's stopped via `onContextMenu={(e) => e.stopPropagation()}`) shows:

* **New Note** → calls `onNewNote()`, which opens the prompt modal in [[App Component]].
* **New Folder** → calls `onNewFolder()`, same prompt modal in folder mode.
* **Paste** (only if `clipboardPath` is set) → calls `onPaste()`.

This duplicates some sidebar context-menu functionality so users don't have to mouse over to the sidebar to perform common actions.

## What TabBar **doesn't** do

* It doesn't render the toolbar buttons (`+`, search, graph). Those are siblings in the title bar — see [[App Component]] and [[Custom Title Bar]].
* It doesn't manage tab content. The active tab's note is rendered by [[Editor Component]] in `.content`.
* It doesn't reorder tabs (no drag-to-reorder). A future improvement.

## Related

* [[App Component]] — owns the tab list and handlers
* [[Tabs]] — feature view
* [[Custom Title Bar]] — surrounding layout
