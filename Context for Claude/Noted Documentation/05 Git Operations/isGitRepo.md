# isGitRepo

**Source:** `electron/fileService.ts` → `isGitRepo(vaultDir)`
**IPC channel:** `git:isRepo`
**Renderer access:** `window.api.isGitRepo(vaultDir)` (also aliased as `gitIsRepo`)

## Signature

```ts
function isGitRepo(vaultDir: string): Promise<boolean>
```

## Implementation

```ts
export function isGitRepo(vaultDir: string): Promise<boolean> {
  return new Promise((resolve) => {
    execFile('git', ['rev-parse', '--is-inside-work-tree'], { cwd: vaultDir }, (err) => {
      resolve(!err)
    })
  })
}
```

`git rev-parse --is-inside-work-tree` exits 0 when run inside a git working tree, non-zero otherwise. We just convert that to a boolean.

The Promise **never rejects** — a non-repo is a successful `false`, not an error. This simplifies callers (no try/catch needed just to detect "no git here").

## Callers

### [[App Component]] (first-run check)

```ts
useEffect(() => {
  if (!vaultDir) return
  const checkGitRepo = async () => {
    try {
      const isRepo = await window.api.isGitRepo(vaultDir)
      setIsGitRepo(isRepo)
      if (!isRepo) {
        setShowGitSetup(true)   // open the git-setup modal
        setGitUrl(''); setGitSetupError(null)
      }
    } catch (error) {
      setIsGitRepo(false); setShowGitSetup(true)
    }
  }
  checkGitRepo()
}, [vaultDir])
```

If the vault is **not** a git repo on startup, the setup modal appears. The user can either provide a remote URL (kicks off the [[gitInit]] → [[gitAddRemote]] → [[gitInitialCommit]] sequence) or skip.

### [[useGitSync]] (sync state)

```ts
const refreshGitStatus = useCallback(async () => {
  if (!vaultDir) return
  try {
    const repo = await window.api.gitIsRepo(vaultDir)
    setIsRepo(repo)
    if (repo) {
      const status = await window.api.gitStatus(vaultDir)
      // …
    }
  } catch {
    setIsRepo(false)
  }
}, [vaultDir])
```

`isRepo` gates whether the rail/sidebar sync button is rendered at all.

### Legacy [[GitPanel Component]]

Same pattern as [[useGitSync]]; this component is no longer used.

## Why two names?

Both `isGitRepo` and `gitIsRepo` are exported in [[preload.ts]]:

```ts
isGitRepo: (vaultDir) => ipcRenderer.invoke('git:isRepo', vaultDir),
gitIsRepo: (vaultDir) => ipcRenderer.invoke('git:isRepo', vaultDir),
```

Different callsites grew different conventions ([[App Component]] uses `isGitRepo`; [[useGitSync]] uses `gitIsRepo`) and rather than rename them, both ended up exported. Functionally identical.

## Related

* [[Git Overview]]
* [[gitStatus]] — typically called right after to check for changes
* [[App Component]] — first-run setup flow
* [[useGitSync]]
