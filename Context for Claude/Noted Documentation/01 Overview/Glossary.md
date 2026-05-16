# Glossary

Quick definitions of recurring terms.

### Active note
The note currently being shown in the [[Editor Component]]. Held in `activeNote` state in [[useVault]]. Distinct from "active tab" (`activeTabIndex` in [[App Component]]) — though usually the same.

### Decoration (ProseMirror)
A visual overlay applied to text without changing the underlying document. Noted uses an inline decoration for `[[wiki links]]` — see [[Wiki Link Plugin]]. Decorations let us style `[[Foo]]` like a clickable link while the raw markdown text stays exactly `[[Foo]]`.

### File tree
Hierarchical tree of folders and notes shown in the sidebar. Built by [[buildFileTree]] in the main process; rendered by [[Sidebar Component]].

### Frameless window
An Electron window with `frame: false` — no native OS title bar. Noted draws its own; see [[Custom Title Bar]].

### Main process
The Electron process running Node.js. Has filesystem and git access. Files: `electron/*.ts`. See [[Process Model]].

### Note
A `.md` file inside the vault. Identified everywhere by its **path** (full absolute path), and displayed by its **name** (filename without `.md`). See [[Types]].

### Phantom node (graph)
A `[[link]]` whose target note doesn't exist. Originally [[useGraph]] rendered these as separate gray nodes; the current implementation skips them entirely (links pointing to missing notes are dropped).

### Preload
The script run before the renderer code, in a privileged context with access to both Node and DOM. Used only to expose `window.api` via Electron's `contextBridge`. See [[preload.ts]].

### Renderer process
The Electron Chromium process running the React app. Sandboxed; no Node access. Files: `src/**/*`.

### Rail
The 38px-wide persistent strip on the left side of the window. Contains the sidebar toggle (in the title bar) and the compact sync icon (in the body). The rail is the [[Window Controls]] drag handle. See [[Custom Title Bar]].

### Selected paths
The set of file/folder paths the user has Ctrl/Shift-clicked in the [[Sidebar Component]]. Lives in `App.tsx` as `sidebarSelectedPaths`. Drives the [[Multi-Select Deletion]] feature.

### Tab
An open note shown in the [[TabBar Component]]. Each tab is `{ path, name }`. Tab list is in [[App Component]]; switching tabs calls [[openNote]] from [[useVault]].

### Top-level folder
A folder directly inside the vault root. Used by [[useFolderColors]] to assign a color per top-level folder; descendants inherit. See [[isTopLevelFolder]] (`useFolderColors.ts`).

### Vault
The root directory Noted treats as the user's knowledge base. Configurable; defaults to the repository root. See [[Vault Configuration]] and [[File Format and Vault]].

### Vault directory
The vault's absolute filesystem path. Stored as `vaultDir` everywhere in the renderer; persisted to `noted-config.json` by the main process.

### Wiki link
The `[[Note Name]]` syntax. Rendered as a styled clickable span in the editor; resolved by [[useVault]]'s `resolveLink`; visualized in the [[Graph View]]. The styling plugin: [[Wiki Link Plugin]]. The feature overview: [[Wiki Links]].

### window.api
The bridge object exposed by [[preload.ts]] on `window.api`. All renderer→main IPC goes through it. Surface defined in [[IPC Channels]] and typed in [[Types]].

## Related

* [[About Noted]]
* [[Process Model]]
* [[Types]]
