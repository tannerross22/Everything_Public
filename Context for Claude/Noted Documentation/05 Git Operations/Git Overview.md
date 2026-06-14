# Git Overview

All git operations in Noted run as **subprocesses** of the external `git` binary via `child_process.execFile`. They live in `electron/fileService.ts` and are exposed through IPC channels prefixed `git:*`.

## Why subprocess instead of a JS library?

Two reasons:

1. **Authentication just works.** If the user has `git` configured with credentials (helper, SSH key, PAT, etc.), every git command Noted runs inherits that configuration. No need to embed credential storage in the app.
2. **Behavior fidelity.** Running `git pull` and `git push` exactly as the user's CLI would produces the same merge results, conflict markers, hooks, etc. as if the user had run them themselves.

## `execFile` not `exec`

```ts
import { execFile } from 'child_process'

execFile('git', ['add', '-A'], { cwd: vaultDir }, (err, stdout, stderr) => { … })
```

* **`execFile`** takes the binary name and an **array** of arguments. No shell interpretation.
* **`exec`** would invoke a shell — vulnerable to injection if any argument contained shell metacharacters (the commit message especially).

See [[Security Model]] for the broader principle. Using `execFile` is a [[Noted App Bugs|long-resolved decision]] — never use string interpolation for git args.

## Function list

| Function | What it runs | IPC channel | Doc |
|---|---|---|---|
| `isGitRepo(vaultDir)` | `git rev-parse --is-inside-work-tree` | `git:isRepo` | [[isGitRepo]] |
| `gitStatus(vaultDir)` | `git status --porcelain` | `git:status` | [[gitStatus]] |
| `gitSync(vaultDir, msg)` | `git add -A`; `commit -m`; `fetch`; possibly `checkout`; `pull -X ours`; `push -u` | `git:sync` | [[gitSync]] |
| `gitLog(vaultDir, n)` | `git log --oneline -<n>` | `git:log` | [[gitLog]] |
| `gitInit(vaultDir)` | `git init` | `git:init` | [[gitInit]] |
| `gitAddRemote(v, name, url)` | `git remote add <name> <url>` | `git:addRemote` | [[gitAddRemote]] |
| `gitGetRemoteUrl(v, name)` | `git config --get remote.<name>.url` | `git:getRemoteUrl` | [[gitGetRemoteUrl]] |
| `gitInitialCommit(v, msg)` | `git add -A`; `commit -m` | `git:initialCommit` | [[gitInitialCommit]] |

## The sync flow at a glance

The non-trivial function is [[gitSync]]. Six commands run sequentially, with conditional behavior on detached HEAD:

```
git add -A
git commit -m <message>
git fetch origin
[ if HEAD is detached: detect 'main' or 'master', git checkout -B <branch> origin/<branch> ]
git pull origin <branch> --allow-unrelated-histories -X ours
git push -u origin <branch> -v
```

Each step is documented in detail in [[gitSync]].

## Where it lives in the renderer

* **State + button:** [[useGitSync]] hook holds `isRepo`, `hasChanges`, `syncing`, `isProcessing`, `showSynced`, and exposes `handleSync()`.
* **Buttons:** rendered both as the compact rail icon in [[App Component]] (when sidebar collapsed) and as the footer button in [[Sidebar Component]].
* **First-run setup:** [[App Component]]'s git setup modal calls [[gitInit]], [[gitAddRemote]], [[gitInitialCommit]] in sequence when the user provides a GitHub URL.
* **Legacy:** [[GitPanel Component]] (now unused) had a self-contained git UI; it was replaced by the rail/sidebar buttons.

## What happens after sync

After [[gitSync]] resolves, [[main.ts]] manually fires `vault:files-changed`:

```ts
ipcMain.handle('git:sync', async (_e, vaultDir, message) => {
  const result = await gitSync(vaultDir, message)
  if (mainWindow) mainWindow.webContents.send('vault:files-changed')
  return result
})
```

This is so any new files pulled from the remote appear in the sidebar.

## Bugs and risks

* [[Noted App Bugs|Bug #9]] — `git add -A` stages **everything** in the vault, which includes the app source and build artifacts when the vault is the repo root. Users should `.gitignore` `dist/`, `dist-electron/`, `node_modules/` to avoid pushing junk.

## Related

* [[Git Sync]] — feature-level view
* [[gitSync]] — the long-form sync logic
* [[useGitSync]] — renderer state hook
* [[fileService.ts]]
