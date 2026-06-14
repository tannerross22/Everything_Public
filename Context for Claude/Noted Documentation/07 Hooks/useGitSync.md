# useGitSync

**Path:** `src/hooks/useGitSync.ts`

Owns all git sync state in the renderer: whether the vault is a repo, whether it has uncommitted changes, whether a sync is in flight, and whether a "Synced!" flash should be shown.

Lives once in [[App Component]]; the resulting state is forwarded to both the [[Custom Title Bar|persistent rail icon]] and the [[Sidebar Component]] footer button so they stay synchronized.

## Signature

```ts
function useGitSync(vaultDir: string): {
  isRepo: boolean
  hasChanges: boolean
  syncing: boolean
  isProcessing: boolean
  showSynced: boolean
  handleSync: () => Promise<void>
}
```

## State

```ts
const [isRepo, setIsRepo] = useState(false)
const [hasChanges, setHasChanges] = useState(false)
const [syncing, setSyncing] = useState(false)         // a sync IPC is in flight
const [isProcessing, setIsProcessing] = useState(false) // file changes settling
const [showSynced, setShowSynced] = useState(false)   // success flash
```

## `refreshGitStatus()`

```ts
const refreshGitStatus = useCallback(async () => {
  if (!vaultDir) return
  try {
    const repo = await window.api.gitIsRepo(vaultDir)
    setIsRepo(repo)
    if (repo) {
      const status = await window.api.gitStatus(vaultDir)
      const lines = status.trim().split('\n').filter(l => l.trim())
      setHasChanges(lines.length > 0)
    }
  } catch {
    setIsRepo(false)
  }
}, [vaultDir])
```

Two IPC calls back to back: [[isGitRepo]] and [[gitStatus]]. Wraps both in try/catch — any failure means "treat as not a repo," which hides the sync UI entirely.

## Three triggers

```ts
useEffect(() => {
  refreshGitStatus()

  let processingTimeout: ReturnType<typeof setTimeout> | null = null
  const unsubscribe = window.api.onFilesChanged(async () => {
    if (processingTimeout) clearTimeout(processingTimeout)
    setIsProcessing(true)
    processingTimeout = setTimeout(async () => {
      await refreshGitStatus()
      setIsProcessing(false)
    }, 1000)
  })

  const interval = setInterval(refreshGitStatus, 30000)

  return () => {
    if (processingTimeout) clearTimeout(processingTimeout)
    unsubscribe()
    clearInterval(interval)
  }
}, [vaultDir])
```

Three independent re-check triggers:

1. **Mount** (and re-mount on `vaultDir` change).
2. **`vault:files-changed` event** from [[File Watcher]]. Debounced 1s so a flurry of writes is one git-status call. While the debounce timer is pending, `isProcessing = true` — used by both sync buttons to show a spinner.
3. **30-second interval** as a fallback in case the watcher missed an event.

## `handleSync()`

```ts
const handleSync = useCallback(async () => {
  if (syncing || !vaultDir) return
  setSyncing(true)
  try {
    const now = new Date()
    const pad = n => String(n).padStart(2, '0')
    const timestamp = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
    await window.api.gitSync(vaultDir, `vault sync: ${timestamp}`)
    await new Promise(r => setTimeout(r, 500))    // let post-sync events settle
    await refreshGitStatus()
    setShowSynced(true)
    setTimeout(() => setShowSynced(false), 2000)
  } catch (error) {
    console.error('[useGitSync] Sync error:', error)
    await refreshGitStatus()
  } finally {
    setSyncing(false)
  }
}, [syncing, vaultDir, refreshGitStatus])
```

* Early-out if already syncing — prevents double-clicks.
* Commit message is a fixed pattern: `vault sync: 2026-05-15 14:23:00`. **Not customizable.**
* After [[gitSync]] resolves, wait 500ms (let [[main.ts]]'s post-sync `vault:files-changed` event propagate), then re-check status.
* `showSynced` flashes for 2 seconds — used by both sync buttons to display "Synced!" briefly.
* On error, refresh status (so the button enables/disables correctly) but don't show a success state.

Errors are logged but not surfaced in the UI here. The legacy [[GitPanel Component]] had a categorized error display; the rail/sidebar buttons just go back to their previous state on failure.

## What it does **not** handle

* **No git setup.** That flow ([[gitInit]] → [[gitAddRemote]] → [[gitInitialCommit]]) lives in [[App Component]] `handleGitSetup`.
* **No log display.** [[gitLog]] is unused.
* **No conflict resolution UI.** [[gitSync]] uses `-X ours`, so the user never sees conflicts.

## Why this is a hook and not a component

The earlier design had a [[GitPanel Component|GitPanel]] component that owned all this state. When the UI was redesigned ([[Custom Title Bar]]), the sync button needed to appear in **two places**: the rail and the sidebar footer. Lifting the state out into a hook and rendering two buttons against the same state is simpler than coordinating two components.

## Related

* [[Git Overview]] — the file-service-side index
* [[gitSync]] — the underlying CLI orchestration
* [[Git Sync]] — feature view
* [[App Component]] — the only consumer
* [[Sidebar Component]] — one of two buttons that consume this state
