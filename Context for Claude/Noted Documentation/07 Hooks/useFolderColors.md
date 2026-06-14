# useFolderColors

**Path:** `src/hooks/useFolderColors.ts`

Manages the **color palette** used for top-level folders, plus the helpers that resolve a path to its top-level folder. The file is named `useFolderColors.ts` but **exports no hook** — only plain helper functions. The "hook" name is historical.

## Exports

```ts
export const FOLDER_PALETTE: string[]        // 10 hex colors
export const DULL_COLOR: string              // gray for un-foldered notes
export function getTopLevelFolder(filePath: string, vaultDir: string): string | null
export function isTopLevelFolder(fullPath: string, vaultDir: string): boolean
export function loadFolderColors(): Record<string, string>
export function assignFolderColor(folderPath: string): string
export function removeFolderColor(folderPath: string): void
```

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

All 10 palette colors come from the **Catppuccin Mocha** palette (the same family used by the rest of the dark theme). `DULL_COLOR` is Catppuccin's `surface2` and is used for any note that doesn't belong to a top-level folder.

## `getTopLevelFolder(filePath, vaultDir)`

```ts
if (!filePath.startsWith(vaultDir)) return null
const sep = vaultDir.includes('\\') ? '\\' : '/'
const relative = filePath.slice(vaultDir.length).replace(/^[/\\]/, '')
const firstSep = relative.search(/[/\\]/)
if (firstSep === -1) return null   // file is at vault root
return vaultDir + sep + relative.slice(0, firstSep)
```

Walks the relative path and returns the first segment as an absolute path. Examples:

| Vault | File path | Returns |
|---|---|---|
| `C:\Vault` | `C:\Vault\Projects\Apollo.md` | `C:\Vault\Projects` |
| `C:\Vault` | `C:\Vault\Projects\sub\thing.md` | `C:\Vault\Projects` |
| `C:\Vault` | `C:\Vault\rootnote.md` | `null` |

Used by [[GraphView Component]] to find each node's "owning" folder for color resolution, and by [[Sidebar Component]] for inheriting colors down a tree.

## `isTopLevelFolder(fullPath, vaultDir)`

```ts
const relative = fullPath.startsWith(vaultDir)
  ? fullPath.slice(vaultDir.length).replace(/^[/\\]/, '')
  : ''
return relative.length > 0 && !relative.includes('\\') && !relative.includes('/')
```

True if `fullPath` is a direct child of `vaultDir`. Used by [[App Component]]:

* On vault load → assigns a color to each existing top-level folder that doesn't have one yet.
* On `handleCreateFolder` → assigns a color when the user creates a new top-level folder.

## Persistence

```ts
const STORAGE_KEY = 'noted_folder_colors'

function load(): Record<string, string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch { return {} }
}

function persist(colors: Record<string, string>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(colors))
}
```

Map of `folderPath → hex color` in `localStorage`. See [[localStorage Keys]] for all the keys Noted uses.

## `assignFolderColor(folderPath)`

```ts
export function assignFolderColor(folderPath: string): string {
  const current = load()
  if (current[folderPath]) return current[folderPath]
  const color = pickUnused(current)
  persist({ ...current, [folderPath]: color })
  return color
}

function pickUnused(existing: Record<string, string>): string {
  const used = new Set(Object.values(existing))
  const free = FOLDER_PALETTE.filter(c => !used.has(c))
  const pool = free.length > 0 ? free : FOLDER_PALETTE
  return pool[Math.floor(Math.random() * pool.length)]
}
```

* Idempotent — returns the existing color if assigned.
* Prefers colors not yet used; once all 10 are taken, picks any random one (collisions inevitable beyond 10 top-level folders).

## `removeFolderColor(folderPath)`

Used when a folder is deleted (to free the color). Currently called in **no place** — folder deletions don't clean up the colors map. Stale entries accumulate harmlessly.

## Where colors flow

1. [[App Component]] calls `loadFolderColors()` once at mount.
2. After each file-tree change, it iterates `fileTree`, finds top-level folder nodes, and calls `assignFolderColor` for any without a color.
3. The resulting `folderColors` state is passed to:
   * [[Sidebar Component]] — for inline tree styling
   * [[GraphView Component]] — for node fills

## Related

* [[Folder Colors]] — feature view
* [[GraphView Component]]
* [[Sidebar Component]]
* [[localStorage Keys]]
* [[App Component]]
