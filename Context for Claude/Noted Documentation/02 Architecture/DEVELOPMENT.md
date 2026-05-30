# Development Guide

This guide covers setting up the development environment and understanding the codebase architecture.

## Quick Start

```bash
git clone <repo>
cd noted-app
npm install
npm run dev
```

The app opens in development mode with hot reload.

## Architecture Overview

```
User clicks Sync button
        ↓
[Frontend] App.tsx calls gitSync.handleSync()
        ↓
[Hook] useGitSync dispatches window.api.syncExecute()
        ↓
[IPC] main.ts routes to syncService.executeSync()
        ↓
[Backend] syncService.ts executes actual git operations
        ↓
File watcher detects changes → vault:files-changed event
        ↓
[Frontend] useVault refreshes file tree
        ↓
UI updates to show synced state
```

## Frontend (`src/`)

### Core Components

**`App.tsx`** (800 LOC)
- Main container orchestrating tabs, sidebar, editor
- Manages: active note, tab bar, vault selection, sync state
- Props flow: `gitSync` state → `Sidebar` → file operations
- Key functions:
  - `openNoteInTab()` — opens note, adds to tab bar
  - `closeTabByPath()` — closes tab and cleans up
  - `handleSync()` — conflict resolution modal logic

**`components/Sidebar.tsx`** (700 LOC)
- Renders file tree, search, sync button
- State: `expandedSet` (which folders are open), `ctxMenu` (context menu)
- Right-click handlers for delete/rename/move/copy
- Multi-select support for bulk operations

**`components/Editor.tsx`** (400 LOC)
- Milkdown editor instance
- Handles save on blur + periodic auto-save
- Detects file changes from other sources (shows reload banner)

### Hooks

**`useVault.ts`** (300 LOC)
- Manages: file tree, file list, active note, selections
- Calls `window.api.listNotes()` and `window.api.buildFileTree()` on mount and file changes
- Provides: `refreshNotes()`, `createNote()`, `deleteNote()`, `renameNote()`

**`useGitSync.ts`** (200 LOC) ⭐ **NEW**
- Manages: sync status, conflicts, error messages
- Periodic refresh every 60s + fast check on file changes
- Exposes: `handleSync(resolutions)` — user calls this, hook drives the full sync flow

**`useModal.ts`**
- Simple modal state and confirm dialog
- Used for: delete confirmation, folder selection, sync conflict resolution

### Types (`types.ts`)

```typescript
interface NoteFile {
  name: string        // filename without .md
  path: string        // absolute path
  modifiedAt: number  // mtime in ms
}

interface FileTreeNode {
  name: string
  type: 'file' | 'folder'
  path: string
  children?: FileTreeNode[]
  modifiedAt?: number  // only for files
}
```

## Backend (`electron/`)

### `main.ts` (400 LOC)

**Lifecycle**:
- `createWindow()` — creates Electron window
- `registerIpcHandlers()` — sets up all IPC routes
- `startWatcher()` — starts chokidar file watcher

**File Operations** (all wrapped in `isWriting` guard):
- `vault:create` → createNote()
- `vault:delete` → deleteNote()
- `vault:write` → writeNote()
- `vault:rename` → renameNote()
- `vault:moveNote` → moveNote()

**Sync Operations**:
- `sync:analyseStatus` → analyseSyncStatus() from syncService
- `sync:execute` → executeSync() from syncService

### `syncService.ts` (300 LOC) ⭐ **NEW**

**Type Definitions**:
```typescript
SyncConflict {
  relativePath: string      // relative to vault root
  localContent: string      // current file content
  remoteContent: string     // remote branch version
}

SyncStatus = 
  | { state: 'up-to-date' }
  | { state: 'local-only'; ahead: number }
  | { state: 'remote-only'; behind: number }
  | { state: 'clean-merge'; ahead; behind }
  | { state: 'diverged'; ahead; behind; conflicts }
  | { state: 'no-remote' }
```

**Core Functions**:

1. **`analyseSyncStatus(vaultDir)`** — Read-only analysis
   ```
   git fetch origin
   git rev-list --left-right --count HEAD...origin/branch
   git diff --name-only HEAD...origin/branch (and vice versa)
   → identify conflicted files (changed on both sides)
   → read both versions via git show
   ```
   Returns: SyncStatus object for UI display

2. **`executeSync(vaultDir, resolutions)`** — Destructive merge
   ```
   git add -A && git commit <timestamp>
   [for each resolved conflict]:
     - if 'keep-local': save local file
     - if 'conflict-note': read both versions, prepare note data
   git pull origin branch -X theirs
   [restore saved files]
   [write conflict notes]
   git add -A && git commit "resolved conflicts"
   git push -u origin branch
   ```
   Returns: SyncResult { success, message, conflictsCreated }

### `fileService.ts` (700 LOC)

**File I/O**:
- `listNotes(vaultDir)` → flat list of all .md files
- `buildFileTree(vaultDir)` → hierarchical tree structure
- `readNote()`, `writeNote()` → file content
- `createNote()`, `deleteNote()`, `renameNote()` → mutations

**Git Operations**:
- `gitStatus()` → git status --porcelain
- `gitSync()` → old combined push+pull (kept for compatibility)
- `gitPull()`, `gitPush()` → separate operations (used by executeSync)

**Utilities**:
- `contentHashFile()` → SHA256 hash of file (for future use)

## State Management Flow

### File State (useVault)

```
[Mount]
  ↓
listNotes() + buildFileTree()
  ↓
[File changes detected by watcher]
  ↓
vault:files-changed IPC
  ↓
useVault.refreshNotes()
  ↓
listNotes() + buildFileTree() again
  ↓
[Re-render with new file tree]
```

### Sync State (useGitSync)

```
[Mount]
  ↓
refreshStatus() → window.api.syncAnalyseStatus()
  ↓
[Every 60s]
  ↓
refreshStatus() again (full git check)

[Also on file changes]
  ↓
refreshLocalStatus() (fast, no fetch)
  ↓
[User clicks Sync]
  ↓
handleSync(resolutions) → window.api.syncExecute()
  ↓
onFilesRefreshed() → refreshNotes() (reload file list)
  ↓
refreshStatus() (re-check sync state)
  ↓
[UI updates: Synced! → back to normal in 2.5s]
```

## Key Design Decisions

### Why Git-Native Over Snapshots?

Original plan used SHA256-hashed snapshots to detect changes. Switched to git-native for:
- **Accuracy** — git tracks actual content, not our hashes
- **Performance** — git operations are optimized and fast
- **Simplicity** — no need to persist snapshot state
- **Safety** — leverages git's proven conflict resolution

### Why Three-Way Merge?

Compares: local vs remote vs common ancestor (base)
- Detects when a file changed on both sides
- Detects when a file was deleted on one side, modified on other
- Detects when both sides made identical changes (safe to merge)

### Why Conflict Notes?

When a file is edited on both devices:
1. Can't automatically choose winner (data loss)
2. Creating a conflict note preserves both versions
3. User can manually review and merge later
4. Enables recovery if user accidentally kept wrong version

## Testing Sync Locally

### Setup Two Vaults

```bash
# Vault 1
mkdir vault1 && cd vault1
git init
git remote add origin https://github.com/you/testvault.git

# Vault 2 (in separate directory)
mkdir vault2 && cd vault2
git clone https://github.com/you/testvault.git .
```

### Test Scenarios

**1. Simple push**:
- Open vault1, create note, click Sync → should push

**2. Simple pull**:
- Edit note in vault2, commit+push manually
- Open vault1, click Sync → should pull new note

**3. Conflict detection**:
- Edit same note in vault1 (don't sync)
- Edit same note in vault2 (don't sync)
- Sync vault2 first → pushes
- Sync vault1 → detects conflict → shows red button → opens modal

**4. Conflict resolution**:
- In modal, choose "Keep Mine" or "Keep Remote"
- After sync, check that correct version was kept

## Debugging

### Enable Verbose Logging

In `syncService.ts`, add console.log to git operations:
```typescript
console.log(`[sync] Running: git ${args.join(' ')}`)
const result = await run('git', args, vaultDir)
console.log(`[sync] Result: ${result.substring(0, 200)}`)
```

### Check Git State Manually

```bash
cd /path/to/vault
git status
git log --oneline -5
git branch -a
git diff HEAD...origin/main
```

### Monitor File Watcher

In `main.ts`, the `[FileWatcher]` logs are already enabled. Watch console during file operations.

## Performance Profiling

### Slow Sync?

1. Check `git fetch origin` — should be <1s
2. Check vault size: `find . -name "*.md" | wc -l`
   - >10k files: sync will be slow, consider splitting vault
3. Check git history: `git log --oneline | wc -l`
   - >100k commits: git operations slow, consider squashing history

### Slow Search?

- Search scans all file content in memory
- For >1000 files, consider:
  - Reducing vault size
  - Implementing indexed search (future feature)

## Common Issues

### "Sync button is grey after creating a file"

File mutation handler didn't emit `vault:files-changed` → fix in main.ts IPC handler

### "Sync reports conflicts but I don't see any"

Conflicts exist in git but haven't been read yet → click Sync button to show modal

### "Conflict note created but original file still has conflict marker"

Conflict note is separate from original. Edit original, delete conflict note, sync again.

### "Files keep appearing/disappearing after sync"

Likely due to `.gitignore` rules. Check:
```bash
git status
git check-ignore -v <filename>
```

## Contributing

### Adding a New Sync Feature

1. Add type to `SyncStatus` or `SyncResult`
2. Implement in `analyseSyncStatus()` or `executeSync()`
3. Wire up IPC handler in `main.ts`
4. Expose in `preload.ts` + `global.d.ts`
5. Call from `useGitSync` in frontend
6. Update SYNC.md documentation

### Modifying File Operations

1. Keep `isWriting` guard consistent
2. Always emit `vault:files-changed` after completion
3. Test with file watcher logs enabled
4. Test both app and sync UI respond correctly

## Resources

- [Electron Docs](https://www.electronjs.org/docs)
- [Git Internals](https://git-scm.com/book/en/v2/Git-Internals)
- [React Hooks](https://react.dev/reference/react/hooks)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
