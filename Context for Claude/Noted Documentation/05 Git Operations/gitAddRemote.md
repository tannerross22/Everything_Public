# gitAddRemote

**Source:** `electron/fileService.ts` → `gitAddRemote(vaultDir, remoteName, remoteUrl)`
**IPC channel:** `git:addRemote`
**Renderer access:** `window.api.gitAddRemote(vaultDir, remoteName, remoteUrl)`

## Signature

```ts
function gitAddRemote(vaultDir: string, remoteName: string, remoteUrl: string): Promise<string>
```

## Implementation

```ts
return new Promise((resolve, reject) => {
  execFile('git', ['remote', 'add', remoteName, remoteUrl], { cwd: vaultDir }, (err) => {
    if (err) reject(err)
    else resolve('Remote added successfully')
  })
})
```

Equivalent to `git remote add <name> <url>` — fails if a remote with the same name already exists.

## Callers

[[App Component]] `handleGitSetup`. The setup form validates the GitHub URL with this regex:

```ts
const urlPattern = /^https:\/\/github\.com\/[\w-]+\/[\w.-]+(?:\.git)?$/i
```

So `https://github.com/user/repo` and `https://github.com/user/repo.git` both work; anything else gets a "Please enter a valid GitHub repository URL" error.

The URL is normalized to always end with `.git`:

```ts
const remoteUrl = gitUrl.trim().endsWith('.git') ? gitUrl.trim() : `${gitUrl.trim()}.git`
await window.api.gitAddRemote(vaultDir, 'origin', remoteUrl)
```

## What kinds of remotes are allowed

Anything `git remote add` accepts — HTTPS, SSH, file paths. The validation regex restricts the **UI** to GitHub HTTPS URLs, but if a programmatic caller passed `git@github.com:user/repo.git`, the function itself wouldn't object.

## Logging

```
[gitAddRemote] Adding remote "origin" to: <vaultDir>
[gitAddRemote] Remote URL: <url>
[gitAddRemote] Success
```

## Related

* [[gitInit]] — must run first
* [[gitInitialCommit]] — usually runs third
* [[gitGetRemoteUrl]] — reads back what was set
* [[App Component]] — the setup modal
