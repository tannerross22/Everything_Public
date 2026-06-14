# buildFileTree

**Source:** `electron/fileService.ts` → `buildFileTree(vaultDir)`
**IPC channel:** `vault:tree`
**Renderer access:** `window.api.buildFileTree(vaultDir)`

## Signature

```ts
function buildFileTree(vaultDir: string): FileTreeNode[]

interface FileTreeNode {
  name: string                  // filename or folder name
  type: 'file' | 'folder'
  path: string                  // absolute path
  children?: FileTreeNode[]     // present on folder nodes
  modifiedAt?: number           // present on file nodes (mtimeMs)
}
```

## What it does

Returns a **hierarchical** list of folders and `.md` files starting at `vaultDir`. Each folder node has a `children` array. The tree mirrors the filesystem 1:1, minus excluded directories.

```ts
function walkDir(dir: string): FileTreeNode[] {
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  const nodes: FileTreeNode[] = []
  for (const entry of entries) {
    if (entry.name.startsWith('.') ||
        entry.name === 'node_modules' || entry.name === 'dist' ||
        entry.name === 'dist-electron' || entry.name === 'assets') continue

    const fullPath = path.join(dir, entry.name)
    if (entry.isFile() && entry.name.endsWith('.md')) {
      nodes.push({ name: …, type: 'file', path: fullPath, modifiedAt: fs.statSync(fullPath).mtimeMs })
    } else if (entry.isDirectory()) {
      nodes.push({ name: entry.name, type: 'folder', path: fullPath, children: walkDir(fullPath) })
    }
  }
  // …sort
}
```

## Excluded directories

Same as [[listNotes]] **plus** `assets`:

* Anything starting with `.`
* `node_modules`, `dist`, `dist-electron`
* `assets` (the [[Image Pipeline]] folder — not user content)

## Sort order (built-in)

```ts
nodes.sort((a, b) => {
  if (a.type !== b.type) return a.type === 'folder' ? -1 : 1
  if (a.type === 'file') return (b.modifiedAt || 0) - (a.modifiedAt || 0)
  return a.name.localeCompare(b.name)
})
```

Folders first (alphabetical), then files (newest first).

### …but this is overridden

The [[App Component]] runs its own `sortFileTree` over the result, honoring the user's chosen sort order (`name-az`, `name-za`, `modified-new`, …) — with folders **always first, alphabetically**. So `buildFileTree`'s sort is effectively a fallback if the renderer doesn't sort.

See [[App Component]] → `sortFileTree` for the renderer-side logic.

## Where it's used in the renderer

| Caller | Purpose |
|---|---|
| [[useVault]] `refreshNotes` | Populates `fileTree` state |
| [[App Component]] | Sorts and passes to [[Sidebar Component]] |
| [[Sidebar Component]] `renderNode` | Recursively renders the tree |

## Performance

Same as [[listNotes]] — a single recursive walk with one `stat` per file. No memoization. Returns plain JSON, which crosses the IPC boundary as a structured-cloned object.

## Bug history

* [[Noted App Bugs|Bug #5]] — original `listNotes` was missing the skip list; `buildFileTree` already had it. The fix copied the skip list into both.

## Related

* [[listNotes]] — flat version
* [[App Component]] — `sortFileTree` (renderer-side re-sort)
* [[Sidebar Component]] — renderer
* [[FileTreeNode|Types]]
