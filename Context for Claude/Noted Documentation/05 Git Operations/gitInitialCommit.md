# gitInitialCommit

**Source:** `electron/fileService.ts` → `gitInitialCommit(vaultDir, message)`
**IPC channel:** `git:initialCommit`
**Renderer access:** `window.api.gitInitialCommit(vaultDir, message)`

## Signature

```ts
function gitInitialCommit(vaultDir: string, message: string = 'Initial commit'): Promise<string>
```

## Implementation

```ts
execFile('git', ['add', '-A'], { cwd: vaultDir }, (err1) => {
  if (err1) return reject(err1)

  execFile('git', ['commit', '-m', message], { cwd: vaultDir }, (err2, stdout, stderr) => {
    if (err2 && err2.message?.includes('nothing to commit')) {
      resolve('No files to commit')   // benign — empty vault
    } else if (err2) {
      reject(err2)
    } else {
      resolve('Initial commit created')
    }
  })
})
```

Two shell commands: `git add -A` then `git commit -m <message>`. Unlike [[gitSync]] this **doesn't** fetch/pull/push — it just stages and commits locally.

The "nothing to commit" branch handles a brand-new empty vault gracefully (resolves rather than rejects).

## Callers

[[App Component]] `handleGitSetup`, the third step of first-run setup:

```ts
await window.api.gitInit(vaultDir)
await window.api.gitAddRemote(vaultDir, 'origin', remoteUrl)
await window.api.gitInitialCommit(vaultDir, 'Initial commit from Noted')
```

After this, the vault is a git repo with at least one commit, ready for [[gitSync]] to push to the remote.

## Why a dedicated function?

Couldn't [[gitSync]] just be called instead? Two reasons it's separate:

1. **No remote yet.** At setup time, the remote is brand new — nothing to fetch from. `gitSync`'s pull would fail or hit "refusing to merge unrelated histories" without `--allow-unrelated-histories`.
2. **No push yet.** The first push happens later (on the user's first manual sync), so the setup flow doesn't need to push.

This keeps the setup deterministic — exactly three local operations, no network round-trip until the user clicks Sync.

## Logging

```
[gitInitialCommit] Creating initial commit in: <vaultDir>
[gitInitialCommit] Message: <message>
[gitInitialCommit] Files staged, creating commit...
[gitInitialCommit] Commit created successfully
```

## Related

* [[gitInit]] — runs first
* [[gitAddRemote]] — runs second
* [[gitSync]] — what the user runs after setup
* [[App Component]] — `handleGitSetup`
