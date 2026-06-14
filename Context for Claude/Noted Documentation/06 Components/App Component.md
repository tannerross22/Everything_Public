# App Component

**Path:** `src/App.tsx`

The top-level React component. Owns the **layout**, every piece of cross-component state, and the wiring between hooks and child components.

It is the **single source of truth** for: open tabs, view mode (editor/graph), modal/prompt visibility, sidebar resize state, multi-select state, git-setup wizard state, sort order, and a half-dozen other UI flags.

## Layout

```
.app  (flex column, 100vh)
├── .title-bar     ←  Custom title bar  (frameless window — see [[Custom Title Bar]])
│   ├── .title-rail-btn          (sidebar toggle)
│   ├── .title-tabs              ([[TabBar Component]])
│   └── .title-controls          (+ search, graph, min, max, close)
└── .body-row      (flex row, fills remainder)
    ├── .app-rail                (persistent 38px strip — sync icon when sidebar collapsed)
    └── .body-content
        ├── [[Sidebar Component]]
        ├── .resize-handle
        └── .content
            └── [[Editor Component]]  or  [[GraphView Component]]
```

Plus floating overlays: prompt modal, git-setup modal, [[SearchBar Component]], [[Modal Component]], [[SettingsPage Component]].

## Hooks used

| Hook | Provides |
|---|---|
| [[useVault]] | All file ops, autosave, active note |
| [[useGraph]] | Graph nodes/edges from `[[wiki links]]` |
| [[useGitSync]] | Git status + handler |
| [[useModal]] | Promise-based React modal confirm |

## Owned state

Selection of the most important pieces (full list ~25):

```ts
const [openTabs, setOpenTabs] = useState<OpenTab[]>([])
const [activeTabIndex, setActiveTabIndex] = useState(-1)
const [viewMode, setViewMode] = useState<ViewMode>('editor')
const [searchVisible, setSearchVisible] = useState(false)
const [findVisible, setFindVisible] = useState(false)
const [showSettings, setShowSettings] = useState(false)
const [sortOrder, setSortOrder] = useState<SortOrder>('name-az')
const [clipboardPath, setClipboardPath] = useState<string | null>(null)
const [folderColors, setFolderColors] = useState<Record<string, string>>(…)
const [sidebarWidth, setSidebarWidth] = useState(savedWidth)
const [sidebarCollapsed, setSidebarCollapsed] = useState(savedCollapsed)
const [isResizing, setIsResizing] = useState(false)
const [isMaximized, setIsMaximized] = useState(false)
const [sidebarSelectedPaths, setSidebarSelectedPaths] = useState<Set<string>>(new Set())
// Prompt modal
const [promptVisible, setPromptVisible] = useState(false)
const [promptValue, setPromptValue] = useState('')
const [promptType, setPromptType] = useState<'note' | 'folder'>('note')
// Git setup modal
const [isGitRepo, setIsGitRepo] = useState(false)
const [showGitSetup, setShowGitSetup] = useState(false)
const [gitUrl, setGitUrl] = useState('')
const [gitSetupLoading, setGitSetupLoading] = useState(false)
const [gitSetupError, setGitSetupError] = useState<string | null>(null)
```

## Major callbacks

### `openNoteInTab(path)`
The canonical way to open a note. Every navigation path (sidebar click, tab click, wiki-link click, graph node click, search result click) funnels through this.

```ts
async (path: string) => {
  setFindVisible(false)              // close find bar on switch
  await openNote(path)                // useVault loads content
  const name = notes.find(n => n.path === path)?.name ?? path.split(/[/\\]/).pop()?.replace(/\.md$/i, '')
  setOpenTabs(prev => {
    const existing = prev.findIndex(t => t.path === path)
    if (existing >= 0) { setActiveTabIndex(existing); return prev }
    const next = [...prev, { path, name }]
    setActiveTabIndex(next.length - 1)
    return next
  })
  setViewMode('editor')
}
```

If the note is already in a tab, switch to it; otherwise append a new tab.

### `closeTab(index)`
Removes a tab, picks a replacement active tab, calls [[openNote]] on it (or `clearActiveNote` if no tabs remain).

### `switchTab(index)`
Updates `activeTabIndex` and calls `openNote(openTabs[index].path)` to load that note's content.

### `resolveLink(linkName)`
Overrides the version from [[useVault]] to use `modal.confirm` from [[useModal]] (React modal) instead of the native confirm. Used by [[Wiki Link Plugin]] click handler — see [[Wiki Links]].

### `handleDeleteItems(items)`
Multi-select deletion. Confirms via `modal.confirm`, dedupes (skips files inside deleted folders), deletes via `window.api`, cleans up open tabs, refreshes notes, clears selection. Full doc in [[Multi-Select Deletion]].

### `handleCreateFolder(fullPath)`
Wraps [[useVault]]'s `createFolder` and additionally calls `assignFolderColor` from [[useFolderColors]] when the new folder is top-level. See [[Folder Colors]].

### `handlePaste(destFolder)`
Reads `clipboardPath` and calls [[copyItem]]. See [[Copy and Paste]].

### `handleGitSetup()`
Validates the GitHub URL, runs [[gitInit]] → [[gitAddRemote]] → [[gitInitialCommit]], updates UI state.

### `handleStartResize(e)`
Begins a sidebar drag-resize. Attaches `mousemove`/`mouseup` listeners to `window`. Persists final width via [[sidebarStorage|saveSidebarState]] on `mouseup`.

## Keyboard handler

A single global `keydown` listener in a `useEffect`. Handles:

* **Ctrl+P** → open [[SearchBar Component]]
* **Ctrl+F** → open [[FindBar Component]]
* **Ctrl+N** → open New Note prompt modal
* **Ctrl+G** → toggle view mode editor ↔ graph
* **Delete** → either multi-delete (if `sidebarSelectedPaths.size > 1`) or delete active note

The handler skips destructive shortcuts when the user is typing in an `<input>`, `<textarea>`, or `contentEditable`.

See [[Keyboard Shortcuts]] for the full table.

## Menu subscriptions

A second `useEffect` subscribes to the three menu events (`menu:newNote`, `menu:openSettings`, `menu:setSortOrder`) and stores the unsubscribe functions for cleanup. See [[Application Menu]].

## Render structure

The JSX is long (~300 lines of return) but logically divided:

1. **Title bar** with rail toggle, [[TabBar Component]], action buttons, window controls.
2. **Body row** with `.app-rail`, [[Sidebar Component]] (when not collapsed), resize handle, content area.
3. **Content area** that renders either `[[Editor Component]]` (with [[FindBar Component]] floating) or `[[GraphView Component]]`, gated by `viewMode`.
4. **Modal overlays** at the end: prompt modal, git setup modal, [[SearchBar Component]], [[Modal Component]], [[SettingsPage Component]].

## Sort logic — `sortFileTree`

```ts
const sortFileTree = useCallback((nodes, order) => {
  const folders = nodes.filter(n => n.type === 'folder')
  const files = nodes.filter(n => n.type === 'file')
  const sortedFolders = folders.sort((a, b) => a.name.localeCompare(b.name))
    .map(node => ({ ...node, children: node.children ? sortFileTree(node.children, order) : undefined }))
  const sortedFiles = files.sort(comparator(order))
    .map(node => ({ ...node, children: node.children ? sortFileTree(node.children, order) : undefined }))
  return [...sortedFolders, ...sortedFiles]
}, [])
```

* **Folders always first**, alphabetical, regardless of the chosen sort. (Implements the "folders A-Z, then files by user order" rule.)
* Recurses into folder children.
* Six sort orders: `name-az`, `name-za`, `modified-new`, `modified-old`, `created-new`, `created-old`. The `created-*` orders currently use `modifiedAt` because creation time is not in [[FileTreeNode]] — effectively the same as the `modified-*` orders.

## Related

* [[Process Model]]
* [[Sidebar Component]], [[TabBar Component]], [[Editor Component]], [[GraphView Component]] — children
* [[useVault]], [[useGraph]], [[useGitSync]], [[useModal]] — hooks consumed
* [[Custom Title Bar]] — the title-bar markup
* [[Multi-Select Deletion]] — `handleDeleteItems` deep dive
