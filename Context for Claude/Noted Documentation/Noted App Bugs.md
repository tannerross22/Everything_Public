# Noted App — Bug Tracker

> Historical bug tracker. Every bug below has been **fixed**. Preserved as a record of design problems and their resolutions. For current behavior, see the linked feature docs.

## Overview

Bugs found via full code review on 2026-05-13. Noted is an Obsidian-like Electron app using Milkdown (ProseMirror), React, D3 graph view, and chokidar file watching.

Each bug below is now linked to the related current documentation so a future reader can see both the original problem and how the fix shaped the implementation.

---

## Bug 1 — `posAtCoords` crash in Editor click handler

* **Severity:** Critical
* **File:** `noted-app/src/components/Editor.tsx:66-68` (at the time)
* **Description:** `view.posAtCoords({left, top})` returns `{pos: number, inside: number} | null`, but the code treated the return value as a raw number and passed it to `view.state.doc.resolve(pos)`. This caused a TypeError at runtime on any click in the editor.
* **Fix:** Destructure the result: `const result = view.posAtCoords(coords); if (result) { ... doc.resolve(result.pos) ... }`. Eventually the custom click handler was removed entirely in favor of ProseMirror's native click handling — see [[Below-content Click Handler]] for the remaining logic.
* **Status:** Fixed
* **Related:** [[Editor Component]], [[Below-content Click Handler]]

---

## Bug 2 — Editor click handler event listener leaks

* **Severity:** Critical
* **File:** `noted-app/src/components/Editor.tsx:74-78` (at the time)
* **Description:** `createEditor()` is async and returned a cleanup function for a click listener, but this return value was never captured or called. Every note switch added another listener.
* **Fix:** Removed the custom click handler entirely (Bug 1 fix made it unnecessary). The current handler that remains, in [[Below-content Click Handler]], properly cleans up.
* **Status:** Fixed
* **Related:** [[Editor Component]]

---

## Bug 3 — File watcher ignores subdirectories

* **Severity:** Critical
* **File:** `noted-app/electron/main.ts:50` (at the time)
* **Description:** The chokidar watcher used `path.join(vaultDir, '*.md')` — non-recursive. `listNotes` and `buildFileTree` recursively walk subdirectories, but the watcher only saw the vault root.
* **Fix:** Change glob to `path.join(vaultDir, '**/*.md')` and add `ignored` patterns for `node_modules`, `dist`, etc.
* **Status:** Fixed
* **Related:** [[File Watcher]], [[main.ts]]

---

## Bug 4 — Context menu delete race condition

* **Severity:** High
* **File:** `noted-app/src/components/Sidebar.tsx:59-65` (at the time)
* **Description:** `handleContextMenuDelete` called `onOpenNote(contextMenu.note.path)` then immediately `onDeleteNote()`. But `openNote` is async (IPC), so `activeNote` hadn't updated yet — it deleted whatever note was *previously* active.
* **Fix:** Inline the delete logic so it doesn't depend on `activeNote` state. The current [[Sidebar Component]] passes file paths directly to delete handlers without depending on the open/active flow.
* **Status:** Fixed
* **Related:** [[Sidebar Component]], [[deleteNote]]

---

## Bug 5 — `listNotes` doesn't skip system directories

* **Severity:** High
* **File:** `noted-app/electron/fileService.ts:28-46`
* **Description:** The `walkDir` inside `listNotes()` only skipped directories starting with `.`. It walked into `node_modules`, `dist`, `dist-electron`. With a vault rooted at the repo, this surfaced hundreds of README.md files in search, graph, and rename-reference-update operations.
* **Fix:** Added the same skip list as `buildFileTree`: `node_modules`, `dist`, `dist-electron`.
* **Status:** Fixed
* **Related:** [[listNotes]], [[buildFileTree]]

---

## Bug 6 — Editor onChange fires on initial load

* **Severity:** Medium
* **File:** `noted-app/src/components/Editor.tsx:36-38`
* **Description:** Milkdown's markdown listener fires when the editor initializes with `defaultValueCtx`, triggering `onChange` → `updateContent` → debounced `writeNote` even though the user hadn't edited anything. This caused an unnecessary write 500ms (now 100ms) after opening any note.
* **Fix:** Added an `initialLoadRef` flag that skips the first callback. See [[Editor Component]] and [[Autosave]].
* **Status:** Fixed
* **Related:** [[Editor Component]], [[Autosave]]

---

## Bug 7 — Search does full content scan on every keystroke

* **Severity:** Medium
* **File:** `noted-app/src/components/SearchBar.tsx:49-64`
* **Description:** `handleSearch` read every note's content via IPC on each keystroke with no debouncing. Large vaults lagged.
* **Fix:** Added a 250ms debounce before starting the content scan. Name matches still appear instantly. See [[SearchBar Component]] and [[Search]].
* **Status:** Fixed
* **Related:** [[Search]], [[SearchBar Component]]

---

## Bug 8 — Dead code files

* **Severity:** Low
* **File:** `noted-app/src/editor/editorSetup.ts`, `noted-app/src/editor/plugins.ts`
* **Description:** These files re-exported Milkdown presets but were never imported by any component. The Editor imported directly from `@milkdown/preset-commonmark`.
* **Fix:** Deleted both files.
* **Status:** Fixed
* **Related:** [[Editor Component]]

---

## Bug 9 — `git add -A` at repo root is risky

* **Severity:** Medium
* **File:** `noted-app/electron/fileService.ts:240`
* **Description:** `gitSync` runs `git add -A` which stages **all** changes in the vault. Since the default vault is the repo root (`Everything_Public`), this stages unrelated files (build artifacts, etc.) alongside note changes. Combined with auto-commit-and-push, this can push unintended changes.
* **Fix:** No code-level fix. The risk is documented and users are expected to `.gitignore` what they don't want pushed. Future improvement: stage only `*.md` files, or add a per-sync confirmation diff.
* **Status:** Acknowledged (no code fix)
* **Related:** [[gitSync]], [[Git Sync]]

---

## Bug 10 — Can't edit after deleting a note (focus trap)

* **Severity:** High
* **Files:** `noted-app/src/components/Sidebar.tsx`, `noted-app/src/App.tsx`, `noted-app/electron/main.ts`, `noted-app/electron/preload.ts`
* **Description:** After deleting a note, the editor unmounted but focus stayed trapped. Clicking a new note in the sidebar mounted the new editor but it never received focus — the user had to alt-tab away and back.
* **Root cause:** `window.confirm()` in Electron's renderer corrupts Chromium's internal focus state in a way that persists until a window-level blur/focus cycle resets it. Clicking within the app (even directly on the contenteditable) couldn't recover.
* **Fix:** Replaced all `confirm()` calls with `window.api.confirm()` routed through `dialog.showMessageBox()` in the main process. Later, [[useModal]] + [[Modal Component]] provided a React-side promise-based confirm that matches the dark theme. **Never use native `confirm()` in the renderer.**
* **Status:** Fixed
* **Related:** [[Security Model]], [[useModal]], [[Modal Component]]

---

## Bug 11 — Can't click below content to start typing

* **Severity:** High
* **File:** `noted-app/src/components/Editor.tsx`
* **Description:** The empty space below the document was not part of ProseMirror's editable area. Clicking there did nothing — the user could only type where existing content existed.
* **Root cause:** `.ProseMirror` had `flex: 1` so it filled the entire editor height. The click handler's early-return `target.closest('.ProseMirror')` fired on every click, so the below-content branch never ran. Also used `state.selection.constructor.near()` (fragile) instead of `TextSelection.near()` imported explicitly.
* **Fix:** Removed the `.ProseMirror` guard; check only whether `clientY <= lastChild.getBoundingClientRect().bottom`. Added `e.preventDefault()` for below-content clicks. Replaced selection with explicit `TextSelection.near()` imported from `@milkdown/prose/state`. See [[Below-content Click Handler]].
* **Status:** Fixed
* **Related:** [[Editor Component]], [[Below-content Click Handler]]

---

## Related

* [[Home]] — documentation hub
* [[Noted App]] — historical design document
* [[Security Model]] — the focus-trap fix lives here in spirit
