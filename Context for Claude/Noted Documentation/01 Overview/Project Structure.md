# Project Structure

The Noted source lives at `Everything_Public/noted-app/`. The documentation you are reading lives at `Everything_Public/Context for Claude/Noted Documentation/` (the path is incidental — Noted finds notes by walking the vault from its configured root; see [[Vault Configuration]]).

## Top-level layout

```
noted-app/
├── package.json                 # deps, scripts, electron-builder config
├── vite.config.ts               # Vite + vite-plugin-electron config
├── tsconfig.json
├── tsconfig.node.json
├── index.html                   # Vite entry — loads src/main.tsx
├── start-noted.bat              # Windows launcher
├── start-noted.vbs              # Silent Windows launcher
├── Create Desktop Shortcut.ps1
├── Noted_logo.png
├── electron/                    # Main process
│   ├── main.ts                  # BrowserWindow, IPC, watcher, menu
│   ├── preload.ts               # contextBridge → window.api
│   └── fileService.ts           # fs + git + image I/O
├── src/                         # Renderer process
│   ├── main.tsx                 # React entry
│   ├── App.tsx                  # Top-level layout, state orchestration
│   ├── App.css                  # ~1500 lines: dark theme + layout
│   ├── types.ts                 # NoteFile, NoteContent, GraphNode, …
│   ├── global.d.ts              # window.api type declarations
│   ├── vite-env.d.ts            # Vite ambient types
│   ├── components/
│   │   ├── Sidebar.tsx          # File tree, multi-select, drag/drop
│   │   ├── TabBar.tsx           # Tabs above editor
│   │   ├── Editor.tsx           # Milkdown wrapper
│   │   ├── GraphView.tsx        # D3 force graph
│   │   ├── SearchBar.tsx        # Ctrl+P fuzzy search
│   │   ├── FindBar.tsx          # Ctrl+F in-note find
│   │   ├── Modal.tsx            # Promise-based confirm dialog
│   │   ├── SettingsPage.tsx     # Placeholder overlay
│   │   ├── FileHeader.tsx       # (legacy — pre-title-bar redesign)
│   │   ├── GitPanel.tsx         # (legacy — superseded by sidebar/rail sync)
│   │   └── NoteContextMenu.tsx  # (legacy — replaced by inline sidebar menu)
│   ├── hooks/
│   │   ├── useVault.ts          # All file ops + autosave
│   │   ├── useGraph.ts          # Parse [[links]] → nodes/edges
│   │   ├── useGitSync.ts        # Git sync state + 30s poll
│   │   ├── useFolderColors.ts   # Top-level-folder color palette
│   │   └── useModal.ts          # Promise-based confirm hook
│   ├── editor/
│   │   └── wikiLinkPlugin.ts    # ProseMirror decoration plugin
│   └── utils/
│       └── sidebarStorage.ts    # localStorage width + collapsed
├── dist/                        # Built renderer (git-ignored)
├── dist-electron/               # Built main + preload (git-ignored)
└── node_modules/
```

## Three logical processes (two real, one external)

1. **Electron Main** — Node.js, full filesystem access. Code under `electron/`. See [[Process Model]].
2. **Renderer** — Chromium sandbox, no Node access. Code under `src/`.
3. **External Git** — invoked from main via `child_process.execFile('git', …)`. See [[Git Overview]].

## Documentation tree (this folder)

```
Noted Documentation/
├── Home.md                          # Index
├── 01 Overview/
├── 02 Architecture/
├── 03 Electron Main/
├── 04 File Operations/
├── 05 Git Operations/
├── 06 Components/
├── 07 Hooks/
├── 08 Editor System/
├── 09 Features/
├── 10 Reference/
├── Noted App.md                     # Original design doc
└── Noted App Bugs.md                # Bug history
```

## Where to look for...

| Looking for | Go to |
|---|---|
| The `BrowserWindow` config | [[main.ts]] |
| `window.api` definition | [[preload.ts]] + [[Types]] |
| Where `[[wiki links]]` are styled | [[Wiki Link Plugin]] |
| How a save reaches disk | [[Data Flow]] |
| Multi-select Delete behavior | [[Multi-Select Deletion]] |
| Git commit + push logic | [[gitSync]] |
| Folder colors persistence | [[useFolderColors]] |
| Sidebar width persistence | [[localStorage Keys]] |

## Related

* [[Tech Stack]] — what each dependency is for
* [[Quick Start]] — npm scripts to build and run
* [[Build and Config]] — `electron-builder`, Vite, TypeScript settings
