# Noted — Obsidian-Like Knowledge App

## Context

Build a personal desktop knowledge management app (like Obsidian) that lives in `Everything_Public/noted-app/`. The app opens its own window, supports live inline markdown editing, wiki-style `[[links]]` between notes, a graph visualization of linked notes, and GitHub sync via git. All notes are plain `.md` files on disk, so edits from Claude Code or any external editor appear automatically.

## Decisions

* **App name:** Noted

* **Default vault:** `Everything_Public` itself (this repo). Git sync uses this repo's existing remote.

* **App directory:** `Everything_Public/noted-app/` (the app code, not the notes)

## Tech Stack

* **Electron** — desktop window (same tech Obsidian uses)

* **React + TypeScript** — UI framework

* **Vite + vite-plugin-electron** — build tooling

* **Milkdown v7** — ProseMirror-based WYSIWYG markdown editor (live inline rendering)

* **D3.js** — force-directed graph visualization

* **chokidar** — file system watching for external changes

* **child\_process.execFile** — git CLI for sync

## Project Structure (\~25 files)

```
noted-app/
├── package.json
├── vite.config.ts
├── tsconfig.json / tsconfig.node.json
├── index.html
├── .gitignore
├── electron/
│   ├── main.ts            # Electron main process, IPC, file watcher
│   ├── preload.ts          # Context bridge (renderer <-> Node.js)
│   └── fileService.ts      # File I/O + git operations
├── src/
│   ├── main.tsx            # React entry
│   ├── App.tsx             # Layout: sidebar + editor/graph toggle
│   ├── App.css             # Dark theme, flexbox layout
│   ├── types.ts            # NoteFile, NoteContent, GraphNode, GraphLink
│   ├── global.d.ts         # window.api type declarations
│   ├── components/
│   │   ├── Sidebar.tsx     # File list, new note button, vault selector
│   │   ├── Editor.tsx      # Milkdown wrapper (remounts per note)
│   │   ├── GraphView.tsx   # D3 force-directed graph
│   │   ├── GitPanel.tsx    # Sync button, status, commit log
│   │   └── SearchBar.tsx   # Name + content search
│   ├── editor/
│   │   ├── editorSetup.ts  # Milkdown plugin config
│   │   └── wikiLinkPlugin.ts  # ProseMirror decoration plugin for [[links]]
│   └── hooks/
│       ├── useVault.ts     # File operations via IPC, autosave
│       └── useGraph.ts     # Parse links, build node/edge data
```

## Implementation Phases

### Phase 1: Scaffold (Electron + React + Vite)

* Create project with `npm init`, install deps: react, react-dom, typescript, vite, @vitejs/plugin-react, vite-plugin-electron, electron

* `electron/main.ts` -- BrowserWindow (1200x800), loads Vite dev server or built HTML

* `electron/preload.ts` -- contextBridge stub

* `src/main.tsx` + `src/App.tsx` -- renders "Noted" placeholder

* **Verify:** `npm run dev` opens an Electron window showing "Noted"

### Phase 2: File System + Sidebar

* `electron/fileService.ts` -- listNotes, readNote, writeNote, createNote, deleteNote

* IPC handlers in main.ts, exposed via preload.ts

* chokidar watcher on vault dir -> sends `vault:files-changed` to renderer

* Vault dir stored persistently (electron-store or JSON config file)

* `src/hooks/useVault.ts` -- React hook for all file ops, 500ms debounced autosave

* `src/components/Sidebar.tsx` -- note list, "+" button, vault directory picker

* `src/App.tsx` -- flexbox layout (250px sidebar + content area), textarea placeholder

* **Verify:** pick vault folder, see .md files listed, create/open/edit notes, external edits auto-refresh

### Phase 3: Milkdown Editor

* Install Milkdown packages: @milkdown/core, ctx, preset-commonmark, preset-gfm, theme-nord, react, plugin-listener, plugin-history

* `src/editor/editorSetup.ts` -- plugin list (commonmark, gfm, history, listener)

* `src/components/Editor.tsx` -- Milkdown React wrapper, `key={noteId}` for remount on note switch

* Replace textarea in App.tsx with `<Editor>`

* **Verify:** type `## Header` -> renders as heading immediately, bold/lists/code work, undo works

### Phase 4: Wiki Links

* `src/editor/wikiLinkPlugin.ts` -- ProseMirror **decoration** plugin (not schema mark)

  * Scans doc for `[[...]]` regex, adds styled inline decorations

  * Click handler extracts target, calls onLinkClick callback

  * Markdown stays as plain `[[text]]` -- no parser/serializer changes needed

* `src/hooks/useVault.ts` -- add resolveLink: find matching note or create new one

* `src/hooks/useGraph.ts` -- regex-extract `[[links]]` from all notes, build GraphNode\[] + GraphLink\[]

* CSS styling for `.wiki-link` (purple, dotted underline, pointer cursor)

* **Verify:** type `[[Other Note]]` -> renders as link, click opens/creates note, .md file has raw `[[]]`

### Phase 5: Graph View

* Install D3 + @types/d3

* `src/components/GraphView.tsx` -- SVG with D3 force simulation

  * forceLink, forceManyBody, forceCenter, forceCollide

  * Nodes colored by existence (real vs phantom), sized by link count

  * Drag + zoom/pan, labels, click -> opens note

* Toggle button in App.tsx toolbar: editor <-> graph view

* **Verify:** 5-6 linked notes render as connected graph, drag/click/zoom all work

### Phase 6: Git Sync

* `electron/fileService.ts` -- gitStatus, gitSync (add -A, commit, push), gitLog, isGitRepo

  * **Security:** use `execFile('git', [...args])` array form, never string interpolation

* IPC handlers + preload exposure

* `src/components/GitPanel.tsx` -- changed file count, sync button with spinner, last 5 commits

* **Verify:** edit notes, click Sync, changes appear on GitHub

### Phase 7: Polish

* Dark theme (CSS variables: dark backgrounds, light text, purple accent)

* Keyboard shortcuts via Electron Menu accelerators: Ctrl+N (new), Ctrl+P (search), Ctrl+G (graph)

* `src/components/SearchBar.tsx` -- filter by name + content search on Enter

* Note deletion (sidebar context menu), empty state onboarding, window title = note name

* **Verify:** shortcuts work, search finds notes, dark theme is consistent

## Key Architecture Decisions

1. **Decoration-based wiki links** -- keeps markdown as plain text, avoids Milkdown parser complexity (\~80 lines vs \~300)
2. **Editor remount on note switch** -- `key={noteId}` instead of imperative doc replacement, avoids cursor/undo bugs
3. **All Node.js access through IPC** -- renderer has zero fs/child\_process access (Electron security best practice)
4. **Debounced autosave (500ms)** -- no manual save needed
5. **chokidar self-write guard** -- skip file-change events triggered by our own writes

## Verification Plan

After each phase, launch with `npm run dev` and test:

* Phase 1: Window opens

* Phase 2: File CRUD works, external edits detected

* Phase 3: Markdown renders inline

* Phase 4: `[[links]]` clickable, notes created

* Phase 5: Graph renders, interactive

* Phase 6: Git sync commits + pushes

* Phase 7: Shortcuts, search, theme all functional

<br />

<br />

![]
