# fileService.ts

**Path:** `electron/fileService.ts`

The OS-touching layer of the main process. Every function here is invoked from an `ipcMain.handle` in [[main.ts]] and exposed to the renderer through [[preload.ts]]. The renderer never imports this file.

## Three concerns, one file

This single file contains three logically distinct groups of functions. Each has its own documentation cluster:

1. **Notes & folders** (filesystem) — [[File Operations]] index
2. **Git CLI** (`child_process.execFile`) — [[Git Overview]]
3. **Image handling** (vault `assets/` folder) — [[Image Pipeline]]

## Types defined here

```ts
export interface NoteFileData {
  name: string         // filename without .md
  path: string         // absolute path
  modifiedAt: number   // mtimeMs from fs.statSync
}

export interface FileTreeNode {
  name: string
  type: 'file' | 'folder'
  path: string
  children?: FileTreeNode[]
  modifiedAt?: number
}
```

These are duplicated on the renderer side in `src/types.ts` ([[Types]]) — kept in sync manually because the two TypeScript projects don't share a `tsconfig`.

## Function index

### Notes & folders
* [[listNotes]] — flat list of every `.md` in the vault
* [[buildFileTree]] — hierarchical tree for the sidebar
* [[readNote]] and [[readNote and writeNote|writeNote]]
* [[createNote]]
* [[deleteNote]]
* [[createFolder and deleteFolder|createFolder]]
* [[createFolder and deleteFolder|deleteFolder]]
* [[moveNote]]
* [[renameNote]] — **also rewrites references in other notes**
* [[copyItem]]

### Git
See [[Git Overview]] for the full set. All shell out via `execFile('git', […args])` — never string interpolation, per the [[Security Model]].

### Images
* [[saveImage]] — write a Buffer to `assets/image-{timestamp}.{ext}`
* [[convertBase64ImagesToFiles]] — find `data:image/...;base64,...` URLs in markdown and replace with file references

## Conventions

* **Errors propagate.** Most functions throw or reject; the IPC handlers don't trap. The renderer's `await` will reject and the React component decides what to do.
* **Paths are absolute.** Everything takes/returns absolute paths.
* **No caching.** Every call hits the disk fresh.
* **Folder exclusion list.** [[listNotes]], [[buildFileTree]] hardcode `node_modules`, `dist`, `dist-electron`, `assets`, and any dotfolder.
* **Cross-platform.** `path.join`, `path.basename`, `path.dirname` everywhere — no manual `/` or `\`.

## Related

* [[main.ts]] — where these are wired to IPC
* [[preload.ts]] — what the renderer sees
* [[Process Model]]
