# Types

The TypeScript type surface. Three files define almost everything:

* `src/types.ts` — domain types used in the renderer
* `src/global.d.ts` — `window.api` declarations (the bridge to main)
* `electron/fileService.ts` — duplicated `NoteFileData` and `FileTreeNode` for main-side use

## Domain types (renderer-side)

### `NoteFile`
```ts
interface NoteFile {
  name: string       // filename without .md
  path: string       // full absolute path
  modifiedAt: number // unix timestamp (mtimeMs)
}
```
Used by:
* [[useVault]] `notes`
* [[SearchBar Component]]
* [[useGraph]] input
* [[NoteContextMenu Component]] (legacy)

### `NoteContent`
```ts
interface NoteContent {
  name: string
  path: string
  content: string    // raw markdown
}
```
Used by:
* [[useVault]] `activeNote`
* [[Editor Component]] indirectly (via `content`, `noteId`)

### `GraphNode`
```ts
interface GraphNode {
  id: string         // note name (display)
  path?: string      // undefined for phantom nodes (currently never present)
}
```
Used by:
* [[useGraph]]
* [[GraphView Component]] (extends with `linkCount` and D3's `SimulationNodeDatum` fields)

### `GraphLink`
```ts
interface GraphLink {
  source: string     // note name
  target: string     // note name
}
```
Used by:
* [[useGraph]]
* [[GraphView Component]] (D3 mutates these in-place to substitute node objects for the ID strings)

### `FileTreeNode`
```ts
interface FileTreeNode {
  name: string
  type: 'file' | 'folder'
  path: string                   // absolute path
  children?: FileTreeNode[]      // present on folders
  modifiedAt?: number            // present on files
}
```
Used by:
* [[useVault]] `fileTree`
* [[App Component]] `sortFileTree`
* [[Sidebar Component]] `renderNode`
* [[buildFileTree]] (main-side; duplicated)

## Component-internal types

These don't live in `types.ts` but are exported from their owning components.

### `OpenTab` (from `TabBar.tsx`)
```ts
interface OpenTab {
  path: string
  name: string
}
```

### `ModalConfig` (from `useModal.ts`)
```ts
interface ModalConfig {
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  isDangerous?: boolean
}
```

### `SidebarState` (from `sidebarStorage.ts`)
```ts
interface SidebarState {
  width: number
  collapsed: boolean
}
```

### `SortOrder` (inline literal in `App.tsx` and `FileHeader.tsx`)
```ts
type SortOrder = 'name-az' | 'name-za' | 'modified-new' | 'modified-old' | 'created-new' | 'created-old'
```

### `ViewMode` (inline in `App.tsx`)
```ts
type ViewMode = 'editor' | 'graph'
```

## `window.api` declaration

`src/global.d.ts` declares the full surface of [[preload.ts]] for TypeScript:

```ts
declare global {
  interface Window {
    api: {
      // Vault directory
      getVaultDir: () => Promise<string>
      selectVaultDir: () => Promise<string | null>

      // File operations
      listNotes: (vaultDir: string) => Promise<NoteFile[]>
      buildFileTree: (vaultDir: string) => Promise<any[]>    // typed as any[] for laziness
      readNote: (filePath: string) => Promise<string>
      writeNote: (filePath: string, content: string) => Promise<void>
      createNote: (vaultDir: string, name: string) => Promise<string>
      deleteNote: (filePath: string) => Promise<void>
      deleteFolder: (folderPath: string) => Promise<void>
      renameNote: (vaultDir: string, oldPath: string, newName: string) => Promise<{ newPath: string; updatedCount: number }>
      createFolder: (folderPath: string) => Promise<string>
      moveNote: (oldPath: string, newFolderPath: string) => Promise<string>
      copyItem: (sourcePath: string, destFolder: string) => Promise<string>

      // File watcher
      onFilesChanged: (callback: () => void) => () => void

      // Menu events
      onMenuNewNote: (callback: () => void) => () => void
      onMenuOpenSettings: (callback: () => void) => () => void
      onMenuSetSortOrder: (callback: (order: string) => void) => () => void

      // Git
      isGitRepo: (vaultDir: string) => Promise<boolean>
      gitIsRepo: (vaultDir: string) => Promise<boolean>     // alias
      gitStatus: (vaultDir: string) => Promise<string>
      gitSync: (vaultDir: string, message: string) => Promise<string>
      gitLog: (vaultDir: string, count: number) => Promise<string>
      gitInit: (vaultDir: string) => Promise<string>
      gitAddRemote: (vaultDir: string, remoteName: string, remoteUrl: string) => Promise<string>
      gitGetRemoteUrl: (vaultDir: string, remoteName?: string) => Promise<string>
      gitInitialCommit: (vaultDir: string, message: string) => Promise<string>

      // Window
      setTitle: (title: string) => Promise<void>
      windowMinimize: () => Promise<void>
      windowToggleMaximize: () => Promise<void>
      windowClose: () => Promise<void>
      windowIsMaximized: () => Promise<boolean>
      confirm: (message: string) => Promise<boolean>

      // Image handling
      saveImage: (vaultDir: string, imageData: ArrayBuffer, imageType: string) => Promise<string>
      convertBase64ImagesToFiles: (vaultDir: string, noteId: string, markdown: string) => Promise<string>
    }
  }
}
```

## Main-side types

In `electron/fileService.ts`:

```ts
export interface NoteFileData {
  name: string
  path: string
  modifiedAt: number
}

export interface FileTreeNode {
  name: string
  type: 'file' | 'folder'
  path: string
  children?: FileTreeNode[]
  modifiedAt?: number
}
```

`NoteFileData` mirrors `NoteFile` in `src/types.ts`; `FileTreeNode` is identical. The duplication is because `electron/` and `src/` use separate `tsconfig` projects and don't share modules.

If the shapes drift apart, IPC results will type-mismatch silently — they cross the boundary as plain objects.

## Related

* [[IPC Channels]] — channel signatures table
* [[preload.ts]] — the runtime implementation
* [[main.ts]] — handlers that match these types
