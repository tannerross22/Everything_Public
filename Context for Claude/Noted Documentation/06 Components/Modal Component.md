# Modal Component

**Path:** `src/components/Modal.tsx`

A simple confirm dialog driven by [[useModal]]. Used in place of the native `window.confirm()` (which is broken on Electron — see [[Noted App Bugs|Bug #10]]) or `window.api.confirm` (which uses a native OS dialog).

## Props

```ts
interface ModalProps {
  title: string
  message: string
  confirmText?: string       // default 'Confirm'
  cancelText?: string        // default 'Cancel'
  onConfirm: () => void
  onCancel: () => void
  isDangerous?: boolean      // styles the confirm button red
}
```

## Render

```tsx
<div className="modal-overlay" onClick={onCancel}>
  <div className="modal-content" onClick={e => e.stopPropagation()}>
    <h2 className="modal-title">{title}</h2>
    <p className="modal-message">{message}</p>
    <div className="modal-buttons">
      <button className="modal-btn modal-btn-cancel" onClick={onCancel}>{cancelText}</button>
      <button className={`modal-btn modal-btn-confirm ${isDangerous ? 'dangerous' : ''}`} onClick={onConfirm}>{confirmText}</button>
    </div>
  </div>
</div>
```

Click outside (the overlay) = cancel. `Escape` = cancel:

```ts
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onCancel()
  }
  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [onCancel])
```

## How it gets rendered

[[App Component]] renders `<Modal>` conditionally based on `modal.isOpen` from [[useModal]]:

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

The Promise-based API in [[useModal]] returns `true` on `handleConfirm`, `false` on `handleCancel`.

## Stylesheet

Imports its own CSS:

```ts
import '../styles/Modal.css'
```

A scoped stylesheet (not part of `App.css`) because the Modal markup lives in many contexts and the styles benefit from being co-located with the component file.

## Where it's used

Any call site that uses `modal.confirm(...)` from [[useModal]] — currently:

* [[App Component]] `handleDeleteItems` (multi-select delete)
* [[App Component]] Delete-key handler for the active note
* [[App Component]] `resolveLink` ("Create new note?" confirmation when clicking a phantom `[[link]]`)
* [[Sidebar Component]] folder/file delete via context menu and header button (it passes `onConfirm={modal.confirm}` down)
* [[Sidebar Component]] header "delete active" button

## Why not native `confirm()`?

[[Noted App Bugs|Bug #10]] documented a focus-trap caused by `window.confirm()` in Electron's renderer. The fix routed confirms either through:

1. `window.api.confirm` → `dialog.showMessageBox` (native OS dialog, see [[main.ts]])
2. `modal.confirm` → this React component

Option 2 is now preferred because it matches the app's dark theme and styles the destructive action prominently.

## Related

* [[useModal]] — the promise-wrapping hook
* [[App Component]] — renders the Modal
* [[Multi-Select Deletion]] — example use case
