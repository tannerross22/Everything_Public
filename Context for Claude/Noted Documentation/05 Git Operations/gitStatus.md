# gitStatus

**Source:** `electron/fileService.ts` → `gitStatus(vaultDir)`
**IPC channel:** `git:status`
**Renderer access:** `window.api.gitStatus(vaultDir)`

## Signature

```ts
function gitStatus(vaultDir: string): Promise<string>
```

Returns the raw stdout of `git status --porcelain`.

## Implementation

```ts
export function gitStatus(vaultDir: string): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile('git', ['status', '--porcelain'], { cwd: vaultDir }, (err, stdout) => {
      if (err) reject(err)
      else resolve(stdout)
    })
  })
}
```

## What `--porcelain` returns

A line-per-file representation, e.g.:

```
 M src/App.tsx
?? new-file.md
 D removed-file.md
```

Each line is `<XY> <path>` where `XY` is a two-character status code (`M`, `A`, `D`, `??` for untracked, etc.).

The renderer doesn't parse the codes — it only counts lines.

## How callers use it

### [[useGitSync]]

```ts
if (repo) {
  const status = await window.api.gitStatus(vaultDir)
  const lines = status.trim().split('\n').filter((l: string) => l.trim())
  setHasChanges(lines.length > 0)
}
```

A non-empty status means "you have uncommitted changes." This drives:
* The sync button's enabled/disabled state.
* The yellow-tinted "has changes" border on both the rail icon and the sidebar footer button.

### Legacy [[GitPanel Component]]

Same logic but stored as `changedCount` for display (`"3 changed"` badge).

## Polling

[[useGitSync]] runs `gitStatus` on three triggers:
1. **Mount.**
2. **Every `vault:files-changed` event** (debounced 1 second).
3. **Every 30 seconds**, as a fallback in case `vault:files-changed` was missed.

The 30-second fallback exists because the watcher can occasionally drop events under load (especially in WSL or virtual FS).

## Logging

Every call logs:

```
[gitStatus] Current status:
 M src/App.tsx
?? new-file.md
```

(Or `[gitStatus] Current status: (no changes)` when clean.) Visible in the dev console — useful when debugging sync issues.

## Related

* [[Git Overview]]
* [[isGitRepo]] — usually called first to gate this
* [[gitSync]] — the action that clears the status
* [[useGitSync]]
