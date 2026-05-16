# useModal

**Path:** `src/hooks/useModal.ts`

A Promise-wrapped confirm dialog. Imperative — call `modal.confirm({...})`, get a `Promise<boolean>`. Renders nothing; pairs with [[Modal Component]] which the consumer renders in JSX.

## Signature

```ts
function useModal(): {
  isOpen: boolean
  config: ModalConfig | null
  confirm: (config: ModalConfig) => Promise<boolean>
  handleConfirm: () => void
  handleCancel: () => void
}

interface ModalConfig {
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  isDangerous?: boolean
}
```

## How the Promise resolves

```ts
const resolveRef = useRef<((value: boolean) => void) | null>(null)

const confirm = useCallback(async (modalConfig) => {
  setConfig(modalConfig)
  setIsOpen(true)
  return new Promise<boolean>(resolve => { resolveRef.current = resolve })
}, [])

const handleConfirm = useCallback(() => {
  resolveRef.current?.(true)
  setIsOpen(false)
  setConfig(null)
  resolveRef.current = null
}, [])

const handleCancel = useCallback(() => {
  resolveRef.current?.(false)
  setIsOpen(false)
  setConfig(null)
  resolveRef.current = null
}, [])
```

The `resolveRef` stores the Promise's `resolve` function. When the user clicks Confirm or Cancel, the corresponding handler resolves the stored Promise with `true` or `false`, then clears state.

## Usage pattern

```ts
const modal = useModal()

// In an async handler:
const confirmed = await modal.confirm({
  title: 'Delete Folder',
  message: 'Delete "Projects" and everything inside it? This cannot be undone.',
  confirmText: 'Delete',
  cancelText: 'Cancel',
  isDangerous: true,
})
if (confirmed) { await deleteFolder(folderPath) }
```

The hook returns immediately; the await suspends the calling code until the user clicks.

## Render pairing

[[App Component]] renders `<Modal>` conditionally:

```tsx
{modal.isOpen && modal.config && (
  <Modal
    title={modal.config.title}
    message={modal.config.message}
    confirmText={modal.config.confirmText}
    cancelText={modal.config.cancelText}
    isDangerous={modal.config.isDangerous}
    onConfirm={modal.handleConfirm}
    onCancel={modal.handleCancel}
  />
)}
```

The hook's state drives visibility, and the handlers complete the Promise.

## Why this pattern?

Two reasons:

1. **Async-friendly.** Promise-based — works inside `async/await` flows without callback nesting.
2. **No native dialogs.** Avoids both `window.confirm()` (which causes [[Noted App Bugs|Bug #10]]) and `window.api.confirm` (which opens an OS dialog that doesn't match the dark theme).

## Where it's used

[[App Component]] is the only consumer; the resulting `modal.confirm` is passed down as the `onConfirm` prop to [[Sidebar Component]] so it can use the same Promise-based dialog for its delete confirmations.

## Limitations

* Only one modal at a time. Calling `confirm` while one is open replaces the previous Promise without resolving the old one — the stale `resolve` is overwritten and the old call hangs forever.
* No "input" variant. The "New Note" / "New Folder" prompt is implemented directly in [[App Component]] with its own state (`promptVisible`, `promptValue`).

## Related

* [[Modal Component]] — the renderer
* [[App Component]] — the consumer
* [[Multi-Select Deletion]] — primary use case
* [[Wiki Links]] — `resolveLink` uses it to ask "Create new note?"
