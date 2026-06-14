# Autosave

Noted has no Save button. Every edit is written to disk automatically, 100ms after the user stops typing.

## The mechanism

The autosave is a single `setTimeout` in [[useVault]]:

```ts
const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

const saveNote = useCallback((filePath: string, content: string) => {
  if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
  saveTimerRef.current = setTimeout(async () => {
    await window.api.writeNote(filePath, content)
  }, 100)
}, [])

const updateContent = useCallback((content: string) => {
  if (!activeNote) return
  setActiveNote(prev => prev ? { ...prev, content } : null)
  saveNote(activeNote.path, content)
}, [activeNote?.path, saveNote])
```

Each call to `updateContent` cancels the previous pending save and schedules a new one 100ms in the future. Continuous typing means continuous rescheduling — the write only happens once the user pauses.

## The full chain

```
User types  →  Milkdown listener fires markdownUpdated
            →  [[Editor Component]] onChange(markdown)        (with optional [[Image Pipeline]] conversion)
            →  [[useVault]].updateContent(markdown)
            →  setActiveNote (immediate, in-memory)
            →  saveNote(path, content) — schedules write 100ms from now
            →  (after 100ms of inactivity)
            →  window.api.writeNote(path, content)            (IPC to main)
            →  [[main.ts]] vault:write handler
            →  isWriting = true (suppress [[File Watcher]])
            →  [[readNote and writeNote|writeNote]]            (fs.writeFileSync)
            →  setTimeout 200ms → isWriting = false, fire vault:files-changed
            →  [[useVault]] onFilesChanged → refreshNotes
```

See [[Data Flow]] Trace 1 for the full end-to-end walk.

## Why 100ms

The original [[Noted App]] plan specified **500ms**. After UI testing, users perceived a 500ms gap as data loss — if they typed something and closed the window quickly, the change wasn't saved. The current 100ms is a compromise:

* Long enough to coalesce rapid keystrokes.
* Short enough that closing the window almost always preserves the change.

There's no race-free guarantee. A user typing the final character of a word and instantly slamming Ctrl+W could lose the last 100ms of input.

A more robust design would intercept `beforeunload` (or Electron's `before-quit`) and flush the pending timeout. Not currently implemented.

## The 200ms write-side guard

After `writeNote` completes, [[main.ts]] holds `isWriting = true` for 200ms before:
1. Clearing the flag.
2. Manually firing `vault:files-changed`.

The 200ms is paired with chokidar's `awaitWriteFinish: 300` — by the time chokidar would naturally fire, we've already fired manually with the flag held high. Result: the renderer sees exactly one `files-changed` event per write.

See [[File Watcher]] for the watcher side, [[readNote and writeNote]] for the write side.

## Whose state of truth wins

The optimistic in-memory update (`setActiveNote` inside `updateContent`) means the editor shows the latest text **immediately**. Even if the eventual write fails, the user keeps seeing what they typed.

If a `vault:files-changed` event arrives between `updateContent` and the actual write, [[useVault]] re-reads the file and replaces `activeNote.content` with whatever's on disk. This can in theory clobber unsaved text — but since the write hasn't happened yet, the disk version is older, and ProseMirror's selection would jump back to whatever was last saved.

In practice this isn't observed because:
* Our own writes are guarded by `isWriting`.
* External edits to the same file at the same instant the user is typing are rare.

## What gets saved

The markdown that's saved is whatever the Milkdown serializer produces. Two cases:

1. **No images:** the markdown is the literal text the user sees, modulo Milkdown's formatting (e.g. `*emph*` vs `_emph_`).
2. **Images:** if a base64 data URL is present, the [[Image Pipeline]] converts it to a file reference **before** the markdown reaches `onChange`, so the saved markdown is already lean.

## Related

* [[useVault]] — owns the timer
* [[Editor Component]] — produces the markdown
* [[File Watcher]] — the guard partner
* [[readNote and writeNote]]
* [[Data Flow]]
