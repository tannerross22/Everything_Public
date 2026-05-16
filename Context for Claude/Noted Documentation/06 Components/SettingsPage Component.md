# SettingsPage Component

**Path:** `src/components/SettingsPage.tsx`

A modal overlay reserved for future user-facing settings. Currently a placeholder.

## Render

```tsx
<div className="settings-overlay" onClick={onClose}>
  <div className="settings-panel" onClick={e => e.stopPropagation()}>
    <div className="settings-header">
      <h1 className="settings-title">Settings</h1>
      <button className="settings-close-btn" onClick={onClose}>✕</button>
    </div>
    <div className="settings-content">
      <p className="settings-placeholder">Settings coming soon...</p>
    </div>
  </div>
</div>
```

Click overlay = close. There is no Escape handler currently.

## How it's opened

* **Ctrl+,** keyboard shortcut → File menu → Settings → `menu:openSettings` IPC event → [[App Component]] subscribes and sets `showSettings = true`.

[[App Component]]:

```tsx
{showSettings && <SettingsPage onClose={() => setShowSettings(false)} />}
```

## What would go here

Future settings ideas (none implemented):
* Theme toggle (light/dark)
* Editor font and size
* Autosave debounce duration
* Default vault path
* Folder color customization (currently random from palette — see [[useFolderColors]])
* Git auto-sync interval
* Export options

The component has its own CSS file (`src/styles/SettingsPage.css`) for the overlay/panel layout, with the App-level styles untouched.

## Related

* [[App Component]] — owns `showSettings` state
* [[Application Menu]] — fires `menu:openSettings`
* [[Keyboard Shortcuts]] — Ctrl+,
