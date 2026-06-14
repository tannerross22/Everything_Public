# Vault-Aware Sync

Noted-app now uses an **Obsidian-like bidirectional vault sync model** instead of simple git push/pull. This ensures all your devices converge to the same vault state, with intelligent conflict detection and resolution.

## How It Works

### Sync States

The sync button reflects your vault's current state:

- **Grey (Up to date)** — Local and remote are identical
- **Yellow (Sync)** — Local or remote has changes (or both, but no conflicts detected)
- **Red (Conflicts)** — Same file was edited on multiple devices
- **Spinner** — Sync in progress
- **Green (Synced!)** — Sync completed successfully (2.5 second flash)
- **Red (Error)** — Sync failed

### Analysis Phase

When you open the app or periodically (every 60 seconds), the sync system:

1. **Fetches from remote** to see the latest state
2. **Counts divergence** — how many commits ahead/behind you are
3. **Scans for conflicts** — uses `git diff --name-only` to find files that changed on both sides
4. **Reads both versions** — for each conflict, reads local file + remote version via `git show`

This analysis is **read-only** — it doesn't change any files.

### Sync Execution

When you click Sync:

1. **Commits local changes** — stages all changes with `git add -A` and commits with timestamp
2. **Fetches remote** — gets latest from origin
3. **Handles divergence**:
   - If remote has changes, you see the conflict resolution modal (if conflicts) or it auto-merges cleanly
   - If you have local changes only, they're pushed immediately
4. **Applies resolutions** — for each conflict you resolved:
   - **"Keep Mine"** — your local version is restored and committed
   - **"Keep Remote"** — remote version is pulled and committed
   - **"Create Conflict Note"** — a new note is created with both versions side-by-side
5. **Pushes everything** — all changes (including conflict notes) are pushed to origin

After sync completes, the app refreshes the file list to show any new files pulled from remote.

## Conflict Resolution

### When Conflicts Occur

A conflict happens when **the same file is edited on two different devices** before either syncs.

Example:
- **Device A**: Edits `notes/todo.md` and syncs (commit pushed to origin)
- **Device B**: Also edits `notes/todo.md` locally (not synced yet)
- **Device B**: Clicks Sync → conflict detected

### How to Resolve

Click the red "Conflicts" button. A modal appears for each conflicted file showing:

1. **Filename** — which file is in conflict
2. **Three resolution options**:
   - **"Keep Mine"** — your edits win, remote version is discarded
   - **"Keep Remote"** — remote edits win, your local version is discarded
   - **"Create Conflict Note"** — both versions are saved in a new note for manual review

### Conflict Notes

If you choose **"Create Conflict Note"**, a new file is created:

```
conflict-todo-1234567890.md
```

Contents show both versions clearly marked:

```markdown
# Sync Conflict: todo

This file was edited on multiple devices...

---

## Your Version (This Device)

[your content here]

---

## Remote Version (Other Device)

[remote content here]

---
```

**After resolving**: Edit the original file to contain your preferred merged content, then delete the conflict note and sync again.

## File Change Detection

The app detects when files are:
- **Created** — new note added
- **Modified** — existing note edited
- **Deleted** — note removed
- **Renamed** — note renamed (preserves content)
- **Moved** — note moved to different folder
- **Copied** — note duplicated

All changes trigger an immediate sync status update, so the button reflects your actual sync state.

## Technical Details

### Backend: `electron/syncService.ts`

Two main functions:

**`analyseSyncStatus(vaultDir)`**
- Non-destructive analysis of vault divergence
- Returns state and conflict details
- Used for display and pre-sync analysis

**`executeSync(vaultDir, resolutions)`**
- Actually performs the sync
- Takes optional user conflict resolutions
- Returns success/failure and conflict note paths

### Git Operations

The sync system uses git's native tools for reliability:

- `git fetch origin` — get remote refs
- `git rev-list --left-right --count` — count ahead/behind commits
- `git diff --name-only` — find changed files
- `git show origin/branch:file` — read remote versions
- `git pull ... -X theirs` — merge with "take remote" strategy
- `git push` — push final state

### Local-Only Sync State

`.noted/sync.json` stores metadata about the last sync (via `.git/info/exclude` so it never pushes).

## Best Practices

1. **Sync before leaving a device** — ensures your work is uploaded before switching
2. **Sync after arriving at a device** — pulls any changes from other devices
3. **Resolve conflicts promptly** — conflict notes take space; merge and delete them
4. **Don't manually edit git history** — let Noted handle all git operations
5. **Keep remote accessible** — sync requires internet; local edits work fine offline but won't sync until remote is reachable

## Troubleshooting

### "Sync" button stays grey

- Local and remote are in sync — nothing to sync
- Try creating/editing/deleting a note to see the button change

### Conflicts keep reappearing

- After creating a conflict note, you must edit the original file AND delete the conflict note
- The original file still shows as conflicted until resolved

### Sync fails with "No remote"

- Remote Git URL is not configured
- Check that the vault is a valid git repository with `origin` remote:
  ```bash
  git remote -v
  ```

### Sync shows changes but button is grey

- Try waiting 60 seconds (periodic refresh) or closing/reopening the app
- Or edit a note to trigger immediate status check

## Architecture Notes

- **No manual git commands needed** — all sync via the UI button
- **Bidirectional** — works across multiple devices automatically
- **Intelligent merging** — detects conflicts at file level, not line level
- **Safe** — always fetches before merging, never force-pushes
- **Atomic** — either entire sync succeeds or fails together
