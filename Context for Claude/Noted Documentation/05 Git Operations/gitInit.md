# gitInit

**Source:** `electron/fileService.ts` → `gitInit(vaultDir)`
**IPC channel:** `git:init`
**Renderer access:** `window.api.gitInit(vaultDir)`

## Signature

```ts
function gitInit(vaultDir: string): Promise<string>
```

## Implementation

```ts
export function gitInit(vaultDir: string): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile('git', ['init'], { cwd: vaultDir }, (err, stdout) => {
      if (err) reject(err)
      else resolve(stdout)
    })
  })
}
```

Runs `git init` in `vaultDir`, creating a `.git/` directory. Idempotent — running it on an existing repo is a no-op.

## Callers

[[App Component]] `handleGitSetup`, called when the user fills in a GitHub URL in the first-run setup modal:

```ts
// Step 1: Initialize git repo
await window.api.gitInit(vaultDir)
// Step 2: Add remote
await window.api.gitAddRemote(vaultDir, 'origin', remoteUrl)
// Step 3: Create initial commit
await window.api.gitInitialCommit(vaultDir, 'Initial commit from Noted')
```

The setup modal appears whenever [[isGitRepo]] returns `false` on launch — see [[App Component]] for the trigger logic.

## Logging

```
[gitInit] Initializing git repo at: <vaultDir>
[gitInit] Success: <stdout>
```

## Related

* [[gitAddRemote]] — usually called right after
* [[gitInitialCommit]] — usually called third in the setup sequence
* [[isGitRepo]] — the trigger for the setup flow
* [[App Component]] — `handleGitSetup`
