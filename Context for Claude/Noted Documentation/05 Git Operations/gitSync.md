# gitSync

**Source:** `electron/fileService.ts` → `gitSync(vaultDir, message)`
**IPC channel:** `git:sync`
**Renderer access:** `window.api.gitSync(vaultDir, message)`

The "Sync to GitHub" button is one click; underneath, this function runs a six-or-seven-step shell sequence.

## Signature

```ts
function gitSync(vaultDir: string, message: string): Promise<string>
```

Resolves to `'Synced successfully'` on success. Rejects with the underlying `execFile` error otherwise.

## The pipeline

```
1. git add -A
2. git commit -m <message>
3. git fetch origin
4. git rev-parse --abbrev-ref HEAD
     │
     ├── If branch is 'HEAD' (detached):
     │     git branch -r                              # list remote branches
     │     pick 'main' if 'origin/main' present, else 'master'
     │     git checkout -B <branch> origin/<branch>   # attach to a proper branch
     │
     └── Otherwise: use the current branch name
5. git pull origin <branch> --allow-unrelated-histories -X ours
6. git push -u origin <branch> -v
```

## Step by step

### 1. `git add -A`
Stages **everything** under the vault — modified, added, deleted. Including files outside the user's intent (build artifacts, etc.) if not `.gitignore`'d. See [[Noted App Bugs|Bug #9]].

### 2. `git commit -m <message>`
The message is `vault sync: YYYY-MM-DD HH:MM:SS` (built by [[useGitSync]] / [[GitPanel Component]]).

If there's nothing to commit, git exits with a non-zero code and stderr `nothing to commit`. **Currently this rejects the Promise** — there's no special-case to treat it as success. The renderer's `useGitSync.handleSync` will see the rejection and fall back to `refreshGitStatus`, which finds no changes and disables the button.

### 3. `git fetch origin`
Pulls in remote refs without merging. Needed so the next steps can see what's on the remote without making changes yet.

### 4. Detached HEAD handling

```ts
execFile('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { cwd: vaultDir }, (errBranch, currentBranch) => {
  let branch = currentBranch.trim()
  if (branch === 'HEAD') {
    // Detached HEAD — list remote branches and check out main or master
    execFile('git', ['branch', '-r'], { cwd: vaultDir }, (errList, branchList) => {
      let targetBranch = 'master'
      if (branchList.includes('origin/main')) targetBranch = 'main'
      execFile('git', ['checkout', '-B', targetBranch, `origin/${targetBranch}`], { cwd: vaultDir }, …)
    })
  } else {
    continueSync(branch)
  }
})
```

A detached HEAD can happen if the user checked out a specific commit hash externally. To keep sync sane, we attach to `main` (preferred) or `master`. This is a heuristic — it would not work for repos with a different default branch.

### 5. `git pull origin <branch> --allow-unrelated-histories -X ours`

Three flags:

* `--allow-unrelated-histories` — permits the merge even if the local and remote histories share no commits (rare but possible if [[gitInit]] created a brand-new repo with the same name as an existing remote).
* `-X ours` — for any merge conflict, prefer **our** (local) version. This makes sync **never** open a conflict dialog on the user; conflicts are silently resolved in favor of local changes.

```ts
execFile('git', ['pull', 'origin', branch, '--allow-unrelated-histories', '-X', 'ours'], …, (err2b, …) => {
  if (err2b) {
    // Try to abort any in-progress rebase/merge (defensive)
    execFile('git', ['rebase', '--abort'], { cwd: vaultDir }, () => {})
    // Don't reject — we still have our commits locally
  }
  // …push…
})
```

> ⚠ The `-X ours` strategy means **remote changes can be silently overwritten** by local ones. This is acceptable for a single-user vault but would be data-loss in a collaborative setting.

If the pull errors, we **swallow it** and proceed to push anyway. The reasoning: a failed pull leaves us with our local commits intact; a subsequent push will either succeed (overwriting remote) or fail in step 6 with a more informative error.

### 6. `git push -u origin <branch> -v`

* `-u` sets the upstream — useful after a detached-HEAD recovery in step 4.
* `-v` adds verbose output to stdout (so we log the push result).

Failures here propagate to the renderer:

```ts
} catch (err: any) {
  // useGitSync just logs
  console.error('[useGitSync] Sync error:', error)
  // GitPanel categorizes:
  //   nothing to commit → "Already up to date"
  //   push http ... → "Push failed: Check git credentials/remote URL"
  //   ENOTFOUND → "Network error: Check internet connection"
  //   else → first 60 chars of error
}
```

## Logging

`gitSync` logs **extensively** — every step's stdout, stderr, and any error. Look for `[gitSync]` prefixed lines in the dev console:

```
[gitSync] ========== STARTING SYNC ==========
[gitSync] Vault: C:/Users/tanne/Everything_Public
[gitSync] Message: vault sync: 2026-05-15 14:23:00
[gitSync] git add -A completed
…
[gitSync] ========== SYNC SUCCESSFUL! ==========
```

This was added because git sync failures used to surface as opaque error messages with no way to tell which step broke.

## Post-sync event

The IPC handler in [[main.ts]] manually fires `vault:files-changed` after `gitSync` resolves:

```ts
ipcMain.handle('git:sync', async (_event, vaultDir, message) => {
  const result = await gitSync(vaultDir, message)
  if (mainWindow) mainWindow.webContents.send('vault:files-changed')
  return result
})
```

This causes [[useVault]] to refresh the file list (so any newly pulled notes appear in the sidebar) and [[useGitSync]] to re-check status (so the "has changes" badge clears).

## Why not use a JS library like `simple-git`?

We considered it. The decision to shell out via `execFile` was made because:
* The user's existing git credential helper handles auth without us.
* Behavior matches what the user would see running `git` themselves.
* The list of operations is small (8 functions).

The cost is platform dependence on `git` being on `PATH`.

## Related

* [[Git Overview]] — index of all git functions
* [[useGitSync]] — renderer state + handler
* [[Git Sync]] — feature view
* [[Data Flow]] — Trace 4 walks through a click → sync
* [[Noted App Bugs|Bug #9]] — `git add -A` risk
