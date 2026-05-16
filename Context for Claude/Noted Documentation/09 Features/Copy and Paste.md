# Copy and Paste

An **in-app clipboard** for files and folders, separate from the OS clipboard. Right-click a sidebar item → "Copy" → right-click a folder → "Paste."

## State

```ts
// in App.tsx
const [clipboardPath, setClipboardPath] = useState<string | null>(null)
```

A single path. Storing it as state (not localStorage) means it doesn't survive a restart. That's intentional: the user expects "Copy + Paste" to be a within-session operation.

## Copy action

* **Sidebar context menu** → "Copy" → `onCopy(node.path)` → `setClipboardPath(node.path)`.

No visual feedback that something was copied. The user just gets a "Paste" option afterward.

## Paste action

Three places offer Paste:

1. **Sidebar context menu on a folder** → "Paste" → `onPaste(folder.path)`.
2. **Sidebar context menu on empty space** → "Paste" → `onPaste(vaultDir)`.
3. **Tab bar context menu** → "Paste" → `onPaste(vaultDir)`.

All wire to [[App Component]] `handlePaste`:

```ts
const handlePaste = useCallback(async (destFolder: string) => {
  if (!clipboardPath) return
  await window.api.copyItem(clipboardPath, destFolder)
  await refreshNotes()
}, [clipboardPath, refreshNotes])
```

The `clipboardPath` is **not** cleared after paste — the user can paste the same item multiple times.

## What gets pasted

[[copyItem]] handles both files and folders. Folders are deep-copied recursively. Filename collisions are resolved by appending `(copy)`, `(copy 2)`, etc.

## Where Paste appears in the UI

Paste menu items are conditionally rendered when `clipboardPath` is set:

```tsx
{clipboardPath && (
  <div className="context-menu-item" onClick={() => { onPaste(node.path); closeCtx() }}>
    Paste
  </div>
)}
```

So a fresh session has no Paste option anywhere until the user Copies something.

## What this doesn't do

* **No Cut.** Cut would move + delete the original. Use [[Drag and Drop]] for that.
* **No OS clipboard integration.** Copying a file in File Explorer doesn't make it pasteable in Noted.
* **No multi-copy.** Only one path can be in the clipboard at a time. Copying overwrites the previous selection.
* **No paste-to-self guard.** Pasting a folder into a descendant of itself would create a recursive copy — see [[copyItem]]. There's no UI prevention; you'd run out of disk first.

## Related

* [[copyItem]] — the IPC + fs implementation
* [[Sidebar Component]] — Copy/Paste context menu items
* [[TabBar Component]] — Paste context menu item
* [[App Component]] — `clipboardPath` state, `handlePaste`
