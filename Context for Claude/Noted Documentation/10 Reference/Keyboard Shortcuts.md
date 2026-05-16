# Keyboard Shortcuts

Every key binding in Noted, where it's handled, and what it does.

## Global

These are registered in [[App Component]]'s keyboard `useEffect`. They fire from anywhere in the window unless the focus is in an `<input>`, `<textarea>`, or `contenteditable` (the editor).

| Shortcut | Action | Where |
|---|---|---|
| **Ctrl+P** | Open vault search overlay | [[SearchBar Component]] |
| **Ctrl+F** | Open in-note find bar | [[FindBar Component]] |
| **Ctrl+N** | New Note prompt modal | [[App Component]] prompt |
| **Ctrl+G** | Toggle editor ↔ graph view | [[GraphView Component]] |
| **Delete** | If ≥2 sidebar items selected → multi-delete; else → delete active note | [[Multi-Select Deletion]] / [[useVault]] |

Ctrl+P and Ctrl+F **do** fire even when focused in an input/editor — the relevant `preventDefault` lets them open their overlays from anywhere.

Ctrl+N and Delete are guarded by `isEditing` (skipped when in input or contenteditable).

## From the Application Menu (native)

Registered as Electron menu accelerators in [[main.ts]] `setupMenu()`. These work everywhere (the OS handles them) and additionally show in the native menu.

| Shortcut | Menu path | Action |
|---|---|---|
| **Ctrl+N** | File → New Note | Fires `menu:newNote` → opens prompt modal |
| **Ctrl+,** | File → Settings | Fires `menu:openSettings` → opens [[SettingsPage Component]] |

Note: Ctrl+N is bound **twice** — once by the menu (native accelerator) and once by the renderer keyboard handler. They both reach the same outcome (the prompt opens) because the renderer handler also opens the prompt. In practice the native menu fires first.

The Sort submenu (File → Sort) items have no accelerators — only mouse access.

## In the editor (Milkdown)

Standard ProseMirror / CommonMark shortcuts, registered by Milkdown's `history` plugin and CommonMark preset:

| Shortcut | Action |
|---|---|
| **Ctrl+Z** | Undo |
| **Ctrl+Shift+Z** / **Ctrl+Y** | Redo |
| **Ctrl+B** | Bold |
| **Ctrl+I** | Italic |
| **Tab** in a list | Indent list item |
| **Shift+Tab** in a list | Outdent list item |
| **Enter** twice | Exit list |
| **`#`-space** at line start | Toggle heading level |
| **`*`-space**, **`-`-space**, **`1.`-space** | Start list |
| **`>`-space** at line start | Blockquote |
| **\`\`\`** + Enter | Code block |
| **Backtick-text-backtick** | Inline code |

These are not configured by Noted — they're Milkdown defaults.

## In the find bar

[[FindBar Component]] keyboard:

| Shortcut | Action |
|---|---|
| **Enter** | Next match |
| **Shift+Enter** | Previous match |
| **Escape** | Close find bar |

## In the search overlay

[[SearchBar Component]] keyboard:

| Shortcut | Action |
|---|---|
| **↓ / ↑** | Navigate results |
| **Enter** | Open selected result |
| **Escape** | Close overlay |

## In modal dialogs

[[Modal Component]] keyboard:

| Shortcut | Action |
|---|---|
| **Escape** | Cancel |

The native prompt modal in [[App Component]] (for New Note / New Folder):

| Shortcut | Action |
|---|---|
| **Enter** | Submit |
| **Escape** | Cancel |

The git setup modal:

| Shortcut | Action |
|---|---|
| **Enter** | Submit (when not already loading) |
| **Escape** | Cancel (resets state) |

## Sidebar selection

Modifier-clicks in the [[Sidebar Component]] (handled in `handleNodeClick`):

| Action | Effect |
|---|---|
| **Click** | Replace selection + default action (open / toggle) |
| **Ctrl/Cmd-click** | Toggle in selection; don't open |
| **Shift-click** | Range select from last anchor |

See [[Multi-Select Deletion]].

## What's not bound

Things you might expect that **aren't** wired:

| Shortcut | Status |
|---|---|
| Ctrl+W (close tab) | Not bound |
| Ctrl+Tab / Ctrl+Shift+Tab (cycle tabs) | Not bound |
| Ctrl+S (save) | Not needed (autosave) |
| Ctrl+O (open) | Not bound |
| Escape (clear sidebar selection) | Not bound |

## Related

* [[App Component]] — owns the global keyboard handler
* [[Application Menu]] — native menu accelerators
* [[Multi-Select Deletion]]
* [[Search]], [[Find in Note]]
