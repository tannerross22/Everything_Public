# Folder Colors

Each top-level folder gets a distinct color from a 10-color palette. The color is applied to:

* The folder icon in the [[Sidebar Component]].
* The note icons of descendants (children inherit).
* The node fill in the [[Graph View]].

This creates visual cohesion: all notes in `Projects/` are pink, all in `Daily/` are green, etc.

## What counts as "top-level"

Direct children of `vaultDir`. So in:

```
vault/
├── Projects/         ← top-level, gets a color
│   └── Apollo/       ← inherits Projects' color
│       └── Notes.md
├── Daily/            ← top-level, gets a different color
└── Standalone.md     ← gray (DULL_COLOR)
```

`Projects/` and `Daily/` get assigned colors. `Apollo/` is **not** top-level, so it doesn't get its own color — instead its descendants inherit from `Projects/`.

`Standalone.md` is at the vault root with no folder, so it's gray (`DULL_COLOR`).

## The palette

```ts
export const FOLDER_PALETTE = [
  '#f38ba8', // red
  '#fab387', // peach
  '#f9e2af', // yellow
  '#a6e3a1', // green
  '#94e2d5', // teal
  '#89dceb', // sky
  '#89b4fa', // blue
  '#f5c2e7', // pink
  '#eba0ac', // maroon
  '#a6d189', // lime
]
export const DULL_COLOR = '#585b70'
```

All from the Catppuccin Mocha palette. See [[useFolderColors]].

## Assignment logic

```ts
function pickUnused(existing) {
  const used = new Set(Object.values(existing))
  const free = FOLDER_PALETTE.filter(c => !used.has(c))
  const pool = free.length > 0 ? free : FOLDER_PALETTE
  return pool[Math.floor(Math.random() * pool.length)]
}
```

* Prefer colors not yet used.
* Once 10+ folders exist, colors repeat (collisions allowed).
* The choice is **random** (not deterministic by folder name).

## Persistence

The map `folderPath → hex` is stored in `localStorage['noted_folder_colors']`. Surviving a restart means the user's "Projects is pink" expectation holds. See [[localStorage Keys]].

## When colors get assigned

1. **App mount** — [[App Component]]'s `useEffect` iterates `fileTree`, finds top-level folders without a color, and calls `assignFolderColor` for each. Persists to localStorage.
2. **Folder creation** — [[App Component]]'s `handleCreateFolder` checks if the new folder is top-level and assigns a color if so.

```ts
const handleCreateFolder = useCallback((fullPath: string) => {
  createFolder(fullPath)
  if (vaultDir && isTopLevelFolder(fullPath, vaultDir)) {
    const color = assignFolderColor(fullPath)
    setFolderColors(prev => ({ ...prev, [fullPath]: color }))
  }
}, [createFolder, vaultDir])
```

## Color resolution per node

The [[Sidebar Component]]'s `renderNode` resolves a node's color by walking up:

```ts
// Pseudo-logic: top-level folders use folderColors[path]; descendants inherit from their parent
```

The [[GraphView Component]] resolves per-node:

```ts
const folder = getTopLevelFolder(d.path, vaultDir)
if (!folder) return DULL_COLOR
return folderColors[folder] ?? DULL_COLOR
```

Both use `getTopLevelFolder` from [[useFolderColors]].

## When colors get removed

`removeFolderColor` exists but is **never called**. Deleted folders leave stale entries in localStorage. Harmless — they just consume tiny amounts of disk and aren't reachable from any UI.

## Limitations

* **No user customization.** Colors are randomly assigned; no UI to set a specific color for a folder.
* **No nested top-level coloring.** Sub-folders can't have their own colors — they're forced to inherit.
* **No light-mode palette.** The palette is dark-theme-only.
* **Collisions beyond 10 folders.** Two folders may end up the same color.

## Related

* [[useFolderColors]] — implementation
* [[GraphView Component]] — consumes for node fills
* [[Sidebar Component]] — consumes for icon tints
* [[App Component]] — initial assignment + creation hook
* [[localStorage Keys]]
