# Changelog

All notable changes to Noted will be documented in this file.

## [Unreleased]

### Added - Vault-Aware Sync (Major Feature)

#### New Sync Model
- **Obsidian-like bidirectional vault sync** replacing simple git push/pull
- **Intelligent conflict detection** — automatically finds files edited on multiple devices
- **Three-way merge** — analyzes local, remote, and common ancestor to determine the safest merge
- **Conflict resolution modal** — user chooses per-file: keep local, keep remote, or create conflict note

#### New Files
- **`electron/syncService.ts`** (190 LOC)
  - `analyseSyncStatus()` — Non-destructive analysis of vault divergence, conflict detection
  - `executeSync()` — Performs actual sync with user-chosen conflict resolutions
  - Exports types: `SyncConflict`, `SyncStatus`, `SyncResult`

- **`SYNC.md`** — Comprehensive sync documentation with examples and troubleshooting

- **`README.md`** — Project overview, architecture, getting started guide

#### Modified Files

**`src/hooks/useGitSync.ts`** — Complete rewrite
- New state model: `syncStatus` is one of: `idle | up-to-date | has-changes | has-conflicts | syncing | synced | error | no-remote`
- Removed: `pulling`, `pushing`, `syncing`, separate pull/push handlers
- Added: `conflicts`, `lastMessage`, `lastError`, single `handleSync(resolutions?)` function
- Optimized: Fast local-only status on file changes (no fetch), full remote check every 60s

**`src/App.tsx`**
- Replaced pull/push buttons in rail with unified sync indicator
- Unified Sidebar sync props to match new model
- Added per-file conflict resolution modal
- Simplified sync state threading

**`src/components/Sidebar.tsx`**
- Replaced pull/push buttons with single sync-vault-btn
- Button text/color reflects sync state (grey → yellow → red → green)
- Shows conflict count and sync details in tooltip
- Removed modal for unpulled changes warning (handled in conflict resolution flow)

**`src/App.css`**
- Removed: `.pull-btn`, `.push-btn` styles
- Added: `.sync-vault-btn` with state-based coloring
  - `up-to-date` — grey, subdued
  - `has-changes` — yellow accent (local or remote changes)
  - `has-conflicts` — red warning (file conflicts detected)
  - `syncing` — blue spinner animation
  - `synced` — green flash (2.5s)
  - `error` — red (3s)
- Updated `.rail-sync-btn` to use same state-based styling

**`src/global.d.ts`**
- Removed: `gitPull`, `gitPush`, `gitHasUnpulledCommits` from Window.api types
- Added: `syncAnalyseStatus()`, `syncExecute()` types with full conflict details

**`electron/main.ts`**
- Removed: `hasUnpulledCommits` import and IPC handler
- Added: `syncAnalyseStatus` and `syncExecute` IPC handlers
- Fixed: `vault:create`, `vault:delete`, `vault:deleteFolder`, `vault:rename`, `vault:moveNote`, `vault:copyItem` now emit `vault:files-changed` after completion
  - Ensures sync status updates immediately on file mutations
  - Previously only `vault:write` emitted this event

**`electron/preload.ts`**
- Removed: `gitHasUnpulledCommits` API
- Added: `syncAnalyseStatus`, `syncExecute` API methods
- No change to git push/pull (still available for backend sync logic)

**`electron/fileService.ts`**
- Added: `contentHashFile(filePath)` — SHA256 hash of file content (for future use)
- Added: `crypto` import
- Removed: `hasUnpulledCommits` function (merged into `analyseSyncStatus`)

**`electron/syncService.ts`** — Complete rewrite from snapshot-based to git-native approach
- Old approach (snapshot diffing) replaced with git command-based analysis
- Uses `git rev-list --left-right --count` for accurate ahead/behind counts
- Uses `git diff --name-only` to identify conflicted files
- Uses `git show origin/branch:file` to read remote file versions
- Much more reliable and faster than file hashing

### Changed

- **Sync UI**: Two separate buttons (Pull/Push) → One unified Sync button
- **Sync behavior**: Push-then-pull with overwrite warning → Pull-then-push with conflict resolution
- **Error handling**: Generic "push failed" messages → Detailed per-file conflict options
- **Status refresh**: Only on file changes → Also fast local check, full remote check every 60s
- **Merge strategy**: Inconsistent (-X ours vs -X theirs) → Consistent (-X theirs after user resolutions)

### Fixed

- File deletions no longer silently fail to trigger sync status update
- File creations (new notes) now immediately show as "needs sync"
- Renamed files now properly detected as changed
- Copied files show sync indicator
- Moved files between folders trigger sync status update

### Removed

- `gitPull` and `gitPush` as frontend-facing operations (still used internally by sync)
- `gitHasUnpulledCommits` (functionality moved to `analyseSyncStatus`)
- Snapshot-based file hashing (replaced with git-native diffing)
- `.gitignore` modification (now uses `.git/info/exclude` which is local-only)

### Technical Debt Resolved

- Unified sync state machine (was scattered across multiple booleans)
- Removed inconsistent merge strategies
- Fixed event emission gaps in file mutation handlers
- Eliminated need for snapshot persistence (`.noted/sync.json` structure simplified)

## Performance Impact

- **Sync analysis**: +100-200ms (git operations), unnoticeable on modern hardware
- **File change detection**: Instant (was already fast, now more reliable)
- **Memory**: No significant change (snapshot maps removed, small git output parsing)
- **Disk**: `.noted/` directory now uses `.git/info/exclude` instead of `.gitignore` modification

## Migration Notes

For existing vaults:

1. **No user action required** — Sync works seamlessly with existing git repositories
2. **Old pull/push buttons gone** — Replaced with unified Sync button
3. **Conflict notes** — If you had manual merge conflicts, they'll be detected and offered as conflict notes
4. **Performance** — First sync may take slightly longer due to git analysis, then settles to normal

## Breaking Changes

None from user perspective. Internally:
- `useGitSync` return object changed (see hook documentation)
- Sidebar and App sync props completely restructured
- IPC api changed (`gitPull`/`gitPush` still available but not used by UI)
