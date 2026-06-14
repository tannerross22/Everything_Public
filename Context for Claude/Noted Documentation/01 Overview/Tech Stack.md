# Tech Stack

Every runtime and library that Noted depends on, with a one-paragraph explanation of why it is present.

## Runtimes

### Electron `^42`
The desktop shell. Provides a Chromium renderer process for the React UI and a Node.js main process for filesystem and git access. The main process is described in [[main.ts]]; the contract between processes is the [[IPC Layer]]. The window is **frameless** (`frame: false`) — Noted draws its own title bar; see [[Custom Title Bar]].

### Node.js (via Electron)
Used by the [[Electron Main Process]] for `fs`, `path`, and `child_process.execFile`. The renderer has no Node access (`nodeIntegration: false`, `sandbox: true`); see [[Security Model]].

## UI

### React `^19`
Renders the entire UI. All state is held in React (no Redux, no Zustand). The top-level component is [[App Component]]; subsidiary components are listed under [[Renderer Components]].

### TypeScript `^6`
Used across both main and renderer. The `window.api` IPC surface is fully typed in [[Types]] (see also `src/global.d.ts`).

## Editor

### Milkdown `^7`
A WYSIWYG markdown editor built on ProseMirror. Noted uses these Milkdown packages:

- `@milkdown/core` — editor factory, plugin system
- `@milkdown/preset-commonmark` — CommonMark parse/serialize
- `@milkdown/preset-gfm` — GitHub-flavored markdown (tables, strikethrough, task lists)
- `@milkdown/plugin-history` — undo/redo
- `@milkdown/plugin-listener` — `markdownUpdated` callback for autosave
- `@milkdown/theme-nord` — base theme (overridden in [[App Component]] CSS)
- `@milkdown/prose` — re-export of ProseMirror primitives (for the custom [[Wiki Link Plugin]])
- `@milkdown/utils` — `$prose` helper for plugin authoring

Milkdown integration lives in [[Editor Component]] and [[Milkdown Integration]].

## Graph

### D3.js `^7`
Used solely for the force-directed graph in [[GraphView Component]]. The simulation combines `forceLink`, `forceManyBody`, `forceCenter`, `forceRadial`, `forceCollide`, plus a custom folder-clustering force. Drag and zoom are also D3 behaviors.

## Filesystem

### chokidar `^5`
Watches the vault directory for `.md` changes. Configured in [[File Watcher]]. The single-process file watcher feeds the renderer through an IPC event (`vault:files-changed`).

## Build / Bundling

### Vite `^8` + `@vitejs/plugin-react` `^6`
Bundles the renderer and provides HMR during `npm run dev`.

### vite-plugin-electron `^0.29`
Compiles [[main.ts]] and [[preload.ts]] into `dist-electron/` and launches Electron in dev mode. See [[Build and Config]].

### vite-plugin-electron-renderer `^0.14`
Lets the renderer `import` from Node-ish packages safely (mostly a no-op given our `nodeIntegration: false` choice).

### electron-builder `^25`
Packages the app into a Windows installer (NSIS) plus a portable `.exe`. The build settings are in `package.json` → `build`; see [[Build and Config]].

### TypeScript compiler `^6`
Two configs:
- `tsconfig.json` — for the renderer and Electron output
- `tsconfig.node.json` — for Vite config (which itself runs in Node)

## Related

* [[Project Structure]] — where each of these libraries is used in the source tree
* [[Quick Start]] — npm scripts that wire them together
