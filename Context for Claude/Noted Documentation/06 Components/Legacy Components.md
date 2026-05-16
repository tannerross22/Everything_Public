# Legacy Components

Three components survive in the repo but are no longer mounted anywhere. They're listed here so a reader doesn't waste time tracing them.

If you delete the imports nothing breaks; they remain because their patterns could be useful starting points for future features.

## GitPanel Component

**Path:** `src/components/GitPanel.tsx`

A self-contained git status / sync UI: collapsed by default, expandable to reveal a "Sync to GitHub" button, a `{N} changed` badge, and a recent-commits list.

Originally rendered inside the sidebar footer. Replaced by:

* The compact sync icon in the [[Custom Title Bar|persistent left rail]] (rendered by [[App Component]]).
* The "Sync" button at the bottom of the [[Sidebar Component]].

Both use the [[useGitSync]] hook for state and the same `handleSync` function. GitPanel's logic was effectively duplicated into that hook.

GitPanel calls [[gitLog]] (the only known caller of `gitLog`) to show recent commits — a feature the current UX lacks.

## FileHeader Component

**Path:** `src/components/FileHeader.tsx`

A "Files" dropdown button intended to live above the file tree. Contained:
* New Note
* Settings
* Sort submenu (six order options)

Replaced by:
* New Note → "+" button in the sidebar header and Ctrl+N.
* Settings → File menu → Settings (Ctrl+,) — see [[Application Menu]].
* Sort → File menu → Sort submenu.

The native menu approach was chosen over an in-app dropdown to keep the title-bar footprint small and to leverage built-in keyboard accelerators.

## NoteContextMenu Component

**Path:** `src/components/NoteContextMenu.tsx`

A standalone context menu component with Rename and Delete options. Was used in an earlier sidebar design where each note row right-click rendered this component.

Replaced by the inline `ctxMenu` state and JSX in [[Sidebar Component]] — which now supports many more actions (Open, Open in New Tab, Copy, Paste, New Note Here, New Folder Here, Rename, Delete, Delete Folder, Delete Selected). All inline, not as a separate component.

The original `[[Noted App Bugs|Bug #4]]` (delete race condition) was in a precursor of this component.

## Related

* [[useGitSync]] — replaced GitPanel
* [[Sidebar Component]] — replaced NoteContextMenu and FileHeader's sidebar entries
* [[Application Menu]] — replaced FileHeader's menu items
* [[Custom Title Bar]] — replaced GitPanel's rail icon role
