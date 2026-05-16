# gitLog

**Source:** `electron/fileService.ts` → `gitLog(vaultDir, count)`
**IPC channel:** `git:log`
**Renderer access:** `window.api.gitLog(vaultDir, count)`

## Signature

```ts
function gitLog(vaultDir: string, count: number = 10): Promise<string>
```

## Implementation

```ts
export function gitLog(vaultDir: string, count: number = 10): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile('git', ['log', '--oneline', `-${count}`], { cwd: vaultDir }, (err, stdout) => {
      if (err) reject(err)
      else resolve(stdout)
    })
  })
}
```

Returns the raw output of `git log --oneline -<count>`:

```
a1b2c3d vault sync: 2026-05-15 14:23:00
4d5e6f7 Add Multi-Select Deletion
89abcde Initial commit from Noted
```

## Callers

**None active.** The function was originally consumed by [[GitPanel Component]] to show a "recent commits" list under the sync button, but that component was removed in favor of the rail/sidebar sync UX. The IPC handler and preload wrapper are still exposed; calling `window.api.gitLog(vaultDir, 5)` returns the last 5 commits if you need them.

## Future use

This would be the foundation for an "undo last sync" or "commit history viewer" feature.

## Related

* [[Git Overview]]
* [[GitPanel Component]] — legacy consumer
