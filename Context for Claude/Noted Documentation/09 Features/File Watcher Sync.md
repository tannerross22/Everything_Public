# File Watcher Sync

How external changes to vault files reach the running app. The full mechanism is in [[File Watcher]] (architecture-level); this page is the feature-level view.

## What this enables

* Edit a note in VS Code → the [[Sidebar Component]] refreshes automatically.
* Pull new notes via [[gitSync]] → they appear in the tree immediately.
* Save a note from Claude Code → next time the user opens it, the new content is loaded.

Combined with the [[File Format and Vault|plain `.md`]] storage, this makes Noted interoperable with any other markdown tool.

## The event channel

`vault:files-changed` is a fire-and-forget event from main → renderer. The payload is nothing — every receiver just calls "refresh."

Two subscribers in the renderer:

1. **[[useVault]]** — re-runs [[listNotes]] + [[buildFileTree]], and re-reads the active note's content.
2. **[[useGitSync]]** — debounces 1s, then re-runs [[gitStatus]] to update the "has changes" indicator.

## What triggers it

| Trigger | Source |
|---|---|
| External `.md` change | chokidar watcher in [[File Watcher]] |
| Internal write (after 200ms guard) | `vault:write` handler in [[main.ts]] |
| Internal create (after 200ms guard) | `vault:create` handler |
| Internal delete (after 200ms guard) | `vault:delete` handler |
| Internal folder delete (after 500ms guard) | `vault:deleteFolder` handler |
| Internal copy (after 500ms guard) | `vault:copyItem` handler |
| Internal rename (after 200ms guard) | `vault:rename` handler |
| After successful [[gitSync]] | `git:sync` handler |

Every mutating IPC fires the event after its own work is done. The watcher is suppressed during these operations (the `isWriting` flag) so we don't get duplicate events.

## What the renderer does

### [[useVault]]

```ts
const unsubscribe = window.api.onFilesChanged(() => {
  refreshNotes()
  if (activeNote) {
    window.api.readNote(activeNote.path).then(content => {
      setActiveNote(prev => prev ? { ...prev, content } : null)
    }).catch(() => setActiveNote(null))
  }
})
```

- **`refreshNotes`** — re-fetches `notes[]` and `fileTree[]`; sidebar re-renders.
- **Re-read active note** — picks up external edits to the open note's text. (But: [[Editor Component]] doesn't observe the new content — see [[Milkdown Integration]]'s caveats.)

### [[useGitSync]]

```ts
const unsubscribe = window.api.onFilesChanged(async () => {
  if (processingTimeout) clearTimeout(processingTimeout)
  setIsProcessing(true)
  processingTimeout = setTimeout(async () => {
    await refreshGitStatus()
    setIsProcessing(false)
  }, 1000)
})
```

- **`isProcessing = true`** immediately — both sync buttons show a spinner.
- 1 second later, re-run [[gitStatus]] and stop spinning. The 1-second debounce lets bursts of writes settle before incurring a git-status call.

## Latency

End-to-end (external save → sidebar refresh):

| Step | Latency |
|---|---|
| File written by external tool | 0 ms |
| chokidar detects change | ~50 ms |
| `awaitWriteFinish` stability check | +300 ms |
| `webContents.send` IPC | <1 ms |
| Renderer subscribers fire | ~few ms |
| [[refreshNotes]] runs `listNotes` + `buildFileTree` | ~tens of ms |
| React re-renders sidebar | <16 ms |

So roughly **400ms** from external save to user-visible refresh, dominated by the stability threshold.

## Known gaps

* **Editor doesn't update for the open note.** If the user has note X open and an external tool saves X, the file state changes but Milkdown's view doesn't. The user has to switch tabs and back. See [[Milkdown Integration]].
* **Watcher misses on busy filesystems.** chokidar can drop events under heavy load (a `git checkout` of thousands of files, or running inside WSL). The 30-second poll in [[useGitSync]] is a safety net for git status; there's no equivalent for [[useVault]] (it relies entirely on events).

## Related

* [[File Watcher]] — architecture
* [[Data Flow]] — Trace 3 walks through an external-edit event
* [[useVault]]
* [[useGitSync]]
* [[main.ts]] — fires the event from every mutating handler
