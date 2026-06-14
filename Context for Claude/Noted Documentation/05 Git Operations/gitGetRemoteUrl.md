# gitGetRemoteUrl

**Source:** `electron/fileService.ts` → `gitGetRemoteUrl(vaultDir, remoteName)`
**IPC channel:** `git:getRemoteUrl`
**Renderer access:** `window.api.gitGetRemoteUrl(vaultDir, remoteName?)`

## Signature

```ts
function gitGetRemoteUrl(vaultDir: string, remoteName: string = 'origin'): Promise<string>
```

Default `remoteName` is `'origin'` (both server-side and in the [[preload.ts]] wrapper).

## Implementation

```ts
return new Promise((resolve, reject) => {
  execFile('git', ['config', '--get', `remote.${remoteName}.url`], { cwd: vaultDir }, (err, stdout) => {
    if (err) reject(err)
    else resolve(stdout.trim())
  })
})
```

Reads `git config remote.origin.url`. Trimmed to remove the trailing newline.

## Callers

**None active.** No code currently invokes this. It exists so future features (e.g. a "View on GitHub" button, or showing the remote URL in [[SettingsPage Component]]) can read the configured remote.

## Related

* [[gitAddRemote]] — the writer counterpart
* [[Git Overview]]
