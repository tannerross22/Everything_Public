# Git Sync

A one-button push-and-pull of the entire vault. Replaces the user manually running `git add`, `commit`, `pull`, `push`.

## The button

Two surfaces, same handler:

* **Compact rail icon** (`.rail-sync-btn`) in the persistent left rail, shown when the sidebar is collapsed.
* **Footer button** (`.sync-btn`) at the bottom of the [[Sidebar Component]], shown when the sidebar is expanded.

Both bind to `gitSync.handleSync` from [[useGitSync]] in [[App Component]].

## Visual states

| State | Trigger | Appearance |
|---|---|---|
| **No repo** | `isRepo === false` | Button hidden entirely |
| **Clean** | `isRepo && !hasChanges && !isProcessing && !syncing` | Dim, disabled |
| **Has changes** | `hasChanges && !syncing` | Yellow border tint |
| **Processing** | `isProcessing` (file watcher debounce active) | Spinner |
| **Syncing** | `syncing` (IPC in flight) | Spinner |
| **Synced!** | `showSynced` (2 sec after success) | Brief flash |

These come from booleans in [[useGitSync]]'s returned object.

## What clicking does

`handleSync` in [[useGitSync]]:

1. Build a commit message: `vault sync: 2026-05-15 14:23:00`.
2. Call `window.api.gitSync(vaultDir, message)` → [[gitSync]] in main, which runs:
   ```
   git add -A
   git commit -m <message>
   git fetch origin
   [if detached HEAD: detect 'main' or 'master' and checkout]
   git pull origin <branch> --allow-unrelated-histories -X ours
   git push -u origin <branch> -v
   ```
3. Wait 500ms for [[main.ts]]'s post-sync `vault:files-changed` event to settle.
4. Re-run [[gitStatus]] to update `hasChanges`.
5. Show `showSynced = true` for 2 seconds.

## First-run setup

If the vault isn't a git repo, the [[App Component]]-owned setup modal appears:

```
Set Up Git Repository

This folder is not a Git repository. To use sync features, connect it to a GitHub repository.

[ GitHub repository URL (https://github.com/username/repo) ]

[Skip for Now]                                  [Set Up Repository]
```

Submit runs three operations in sequence:

```ts
await window.api.gitInit(vaultDir)                                              // [[gitInit]]
const remoteUrl = gitUrl.trim().endsWith('.git') ? gitUrl.trim() : `${gitUrl.trim()}.git`
await window.api.gitAddRemote(vaultDir, 'origin', remoteUrl)                    // [[gitAddRemote]]
await window.api.gitInitialCommit(vaultDir, 'Initial commit from Noted')        // [[gitInitialCommit]]
```

No push at setup time — the first push happens on the user's first manual Sync.

## Conflict resolution policy

`-X ours` in the pull means: for any merge conflict, prefer **our** local version. Conflicts are silently resolved in favor of the local copy.

This makes sync "just work" without ever showing the user a conflict dialog, at the cost of potentially overwriting remote changes. Acceptable for a single-user vault; **not** safe for collaboration.

## Status polling

[[useGitSync]] runs [[gitStatus]] on three triggers (mount, file-change debounce, 30 sec interval) to keep the `hasChanges` indicator current. See [[gitStatus]].

## Things that aren't surfaced

* **Commit history.** [[gitLog]] is implemented but no UI shows it.
* **Remote URL.** [[gitGetRemoteUrl]] is implemented but unused. A future "Settings → Git" page could display and let the user change the remote.
* **Branch.** Always uses whatever HEAD points at (or recovers to `main`/`master` if detached). No branch-switching UI.
* **Auth credentials.** Inherits whatever the user's `git` CLI is configured with (credential helper, SSH key, PAT). If sync fails with auth, the user gets an error — no in-app credential prompt.

## Known risks

* [[Noted App Bugs|Bug #9]] — `git add -A` stages **everything** in the vault, including build artifacts if the vault is the repo root. Users must `.gitignore` what they don't want pushed.
* **Silent merge resolution** — `-X ours` can lose remote changes. A user editing the same note on two machines and syncing both directions can lose one side's edits.
* **Push to wrong branch.** Detached HEAD recovery picks `main` or `master` — for repos with a different default branch, this would push to the wrong branch.

## Related

* [[Git Overview]] — function index
* [[gitSync]] — the long-form CLI orchestration
* [[useGitSync]] — renderer state
* [[App Component]] — first-run setup modal
* [[Data Flow]] — Trace 4 walks through a sync click
