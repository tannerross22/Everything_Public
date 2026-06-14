# Noted

A cross-device markdown note-taking app with bidirectional vault sync, built with Electron, React, and Git.

## Features

- **📝 Markdown Editor** — Edit notes in a clean, distraction-free editor powered by Milkdown
- **🔗 Wiki-style Links** — Link between notes with `[[references]]`
- **🗂️ Folder Organization** — Organize notes in nested folders
- **🔍 Full-Text Search** — Find notes by content or title
- **🔄 Bidirectional Sync** — Keep multiple devices in sync with conflict detection
- **🌙 Dark Mode** — Eye-friendly dark theme
- **💾 Auto-Save** — Changes save instantly as you type
- **📊 Graph View** — Visualize connections between notes

## Getting Started

### Requirements

- Node.js 16+
- Git (for sync functionality)
- A GitHub repository (for syncing between devices)

### Installation

```bash
cd noted-app
npm install
npm run dev
```

The app opens on `localhost:5173` for development, or as an Electron desktop app.

### Build

```bash
npm run build
```

Creates optimized builds in `dist/` (web), `dist-electron/` (main process), and `dist-electron/preload.js` (preload).

## Sync

Noted uses a vault-aware sync model inspired by Obsidian Sync. Your notes live in a git repository, and syncing merges changes intelligently across devices.

**[See SYNC.md for detailed sync documentation](./SYNC.md)**

### Quick Start

1. Initialize a vault as a git repository:
   ```bash
   git init
   git remote add origin https://github.com/you/vault.git
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```

2. In Noted, the "Sync" button will be available
3. Click to pull changes from other devices, push local changes, or resolve conflicts

## Architecture

### Frontend (`src/`)

- **`App.tsx`** — Main component, orchestrates tabs, sidebar, sync state
- **`hooks/`** — React hooks (useVault, useGitSync, useModal, etc.)
- **`components/`** — Reusable UI components (Editor, Sidebar, Modal, SearchBar)
- **`types.ts`** — TypeScript interfaces

### Backend (`electron/`)

- **`main.ts`** — Electron main process, IPC handlers, window lifecycle
- **`preload.ts`** — Secure IPC bridge to renderer
- **`fileService.ts`** — File I/O, git operations, hashing
- **`syncService.ts`** — Vault-aware sync logic, conflict detection

### Styling (`src/`)

- **`App.css`** — All component styles (BEM-ish naming)
- **`index.css`** — Global styles and CSS variables

## Project Structure

```
noted-app/
├── electron/              # Electron main process + backend services
│   ├── main.ts           # App lifecycle, IPC, file watcher
│   ├── preload.ts        # Secure API bridge
│   ├── fileService.ts    # File I/O and git operations
│   └── syncService.ts    # Vault-aware sync and merging
├── src/                  # React frontend
│   ├── components/       # UI components
│   ├── hooks/           # Custom React hooks
│   ├── App.tsx          # Main component
│   ├── App.css          # Styles
│   └── types.ts         # TypeScript types
├── .noted/              # Sync metadata (git-ignored)
├── SYNC.md             # Sync documentation
└── package.json
```

## Development

### Key Technologies

- **Electron** — Desktop framework
- **React 18** — UI library
- **TypeScript** — Type safety
- **Vite** — Build tool and dev server
- **Milkdown** — Markdown editor
- **Chokidar** — File system watcher
- **Git** — Version control and sync backend

### Available Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server + Electron |
| `npm run build` | Build all bundles |
| `npm run preview` | Preview production build |
| `npm test` | Run tests (if configured) |

### Hot Module Reload (HMR)

During development, changes to React components hot-reload without losing state. Electron main process changes require a manual restart.

### Debugging

**Frontend**: Use DevTools in Electron window (Cmd+Option+I / Ctrl+Shift+I)  
**Main Process**: Console output appears in terminal

## File Sync Details

### How Sync Works

1. **Analyze** — Checks git divergence and detects file-level conflicts
2. **Resolve** — If conflicts exist, user chooses how to resolve each
3. **Merge** — Commits local changes, pulls remote, applies resolutions
4. **Push** — Pushes final merged state to origin

### Conflict Detection

Conflicts occur when the **same file is edited on two devices** before either syncs. The sync UI detects this automatically and asks you to resolve before merging.

**Resolution options**:
- Keep your version
- Keep remote version  
- Create a conflict note with both versions for manual review

## Folder Structure & Metadata

- **Vault root** — Contains all `.md` files in nested folders
- **`.git/`** — Standard git repository
- **`.git/info/exclude`** — Local-only git ignore (for `.noted/`)
- **`.noted/`** — Sync metadata (never committed)

## Performance Notes

- **First load** — Walks entire vault to build file tree (~100ms for 1000 files)
- **Incremental updates** — File watcher detects changes and only refreshes affected sections
- **Search** — Full-text scan (can be slow for very large vaults)
- **Sync** — Fetches remote state on every sync (requires network)

## Known Limitations

- **Search is in-memory** — No indexing; large vaults may search slowly
- **No real-time collaboration** — Sync is device-to-device, not live co-editing
- **Conflict notes are manual** — After creating a conflict note, you must manually merge and delete it
- **No encryption** — Vault contents are in plain text on disk and git

## Contributing

Contributions welcome! Areas for improvement:

- [ ] Search indexing for faster queries
- [ ] Custom sync strategy (e.g., always keep remote, always keep local)
- [ ] Undo/redo across file operations
- [ ] Bulk operations (rename folders, batch delete)
- [ ] Plugin system for extensions
- [ ] End-to-end encryption

## License

MIT
