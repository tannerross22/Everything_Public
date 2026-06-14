# listNotes

**Source:** `electron/fileService.ts` → `listNotes(vaultDir)`
**IPC channel:** `vault:list` (registered in [[main.ts]])
**Renderer access:** `window.api.listNotes(vaultDir)` (defined in [[preload.ts]])

## Signature

```ts
function listNotes(vaultDir: string): NoteFileData[]

interface NoteFileData {
  name: string         // filename without .md
  path: string         // absolute path
  modifiedAt: number   // mtimeMs
}
```

## What it does

Returns a **flat array** of every `.md` file under `vaultDir`, sorted by modification time (newest first).

```ts
function walkDir(dir: string) {
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isFile() && entry.name.endsWith('.md')) {
      const stat = fs.statSync(fullPath)
      notes.push({ name: entry.name.replace(/\.md$/, ''), path: fullPath, modifiedAt: stat.mtimeMs })
    } else if (entry.isDirectory() && !entry.name.startsWith('.') &&
               entry.name !== 'node_modules' && entry.name !== 'dist' && entry.name !== 'dist-electron') {
      walkDir(fullPath)
    }
  }
}
```

## Excluded directories

* Anything starting with `.` (e.g. `.git`, `.vscode`)
* `node_modules`
* `dist`
* `dist-electron`

> ⚠ Note: unlike [[buildFileTree]], this **does not** exclude `assets/`. Markdown files inside `assets/` (which shouldn't normally exist) would appear in the flat list but not in the sidebar tree. In practice `assets/` only contains images.

This list is hardcoded (originally a bug — see [[Noted App Bugs|Bug #5]] — fixed by adding the same skip list as [[buildFileTree]]).

## Where it's used in the renderer

| Caller | Purpose |
|---|---|
| [[useVault]] `refreshNotes` | Flat list of notes for [[useGraph]], [[SearchBar Component]], [[Wiki Links]] resolution |
| [[renameNote]] (internally in main) | Iterate every note to update `[[wiki link]]` references |

The flat list is *not* what the [[Sidebar Component]] uses — that uses [[buildFileTree]] for hierarchy. The flat list is for:

* **Search.** [[SearchBar Component]] iterates `notes[]` to match names.
* **Graph.** [[useGraph]] iterates `notes[]`, reads each, scans for `[[links]]`.
* **Wiki link resolution.** `resolveLink` in [[useVault]] and [[App Component]] does `notes.find(n => n.name.toLowerCase() === linkName.toLowerCase())`.

## Sort order

```ts
notes.sort((a, b) => b.modifiedAt - a.modifiedAt)
```

Newest first. The [[Sidebar Component]] does **its own** sort (folder-first, then by user-chosen [[Keyboard Shortcuts|sort order]]) via `sortFileTree` in [[App Component]] — `listNotes`' sort is mostly irrelevant.

## Performance

For a vault with ~1000 notes (which is typical), this is fast (~tens of ms). The cost is `fs.statSync` per file. There is no caching — each call walks fresh. The flat list is recomputed on every `refreshNotes` call ([[File Watcher]] events, vault changes).

## Related

* [[buildFileTree]] — the tree alternative used by the sidebar
* [[renameNote]] — consumes the flat list
* [[useGraph]] — consumes the flat list
* [[Search]]
