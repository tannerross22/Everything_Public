---
title: Noted App — Bug Tracker
category: Software / Electron App
status: Active
last_updated: 2026-05-13
tags: [noted, electron, milkdown, bugs, react]
related_files:
  - noted-app/src/components/Editor.tsx
  - noted-app/electron/main.ts
  - noted-app/electron/fileService.ts
  - noted-app/src/components/Sidebar.tsx
  - noted-app/src/components/SearchBar.tsx
---

# Noted App — Bug Tracker

## Overview
Bugs found via full code review on 2026-05-13. Noted is an Obsidian-like Electron app using Milkdown (ProseMirror), React, D3 graph view, and chokidar file watching.

---

## Bug 1 — `posAtCoords` crash in Editor click handler
**Severity:** Critical  
**File:** `noted-app/src/components/Editor.tsx:66-68`  
**Description:** `view.posAtCoords({left, top})` returns `{pos: number, inside: number} | null`, but the code treats the return value as a raw number and passes it directly to `view.state.doc.resolve(pos)`. This causes a TypeError at runtime whenever the user clicks in the editor area, since `resolve()` expects a number argument.  
**Fix:** Destructure the result: `const result = view.posAtCoords(coords); if (result) { ... doc.resolve(result.pos) ... }`. Also consider removing this handler entirely since ProseMirror handles click-to-position natively.  
**Status:** Fixed

## Bug 2 — Editor click handler event listener leaks
**Severity:** Critical  
**File:** `noted-app/src/components/Editor.tsx:74-78`  
**Description:** `createEditor()` is an async function that returns a cleanup function for the click event listener, but this return value is never captured or called. The `useEffect` cleanup only destroys the editor instance. Every time the component re-mounts (switching notes), a new listener is added but the old one is never removed.  
**Fix:** Remove the custom click handler entirely (Bug 1 fix makes it unnecessary since ProseMirror handles this natively), or properly store and invoke the cleanup.  
**Status:** Fixed

## Bug 3 — File watcher ignores subdirectories
**Severity:** Critical  
**File:** `noted-app/electron/main.ts:50`  
**Description:** The chokidar watcher uses `path.join(vaultDir, '*.md')` which only watches `.md` files in the vault root. But `listNotes()` and `buildFileTree()` recursively walk subdirectories. Notes created/modified in subfolders won't trigger the file-change event, so the sidebar won't auto-refresh.  
**Fix:** Change glob to `path.join(vaultDir, '**/*.md')` and add `ignored` patterns for `node_modules`, `dist`, etc.  
**Status:** Fixed

## Bug 4 — Context menu delete race condition
**Severity:** High  
**File:** `noted-app/src/components/Sidebar.tsx:59-65`  
**Description:** `handleContextMenuDelete` calls `onOpenNote(contextMenu.note.path)` then immediately `onDeleteNote()`. But `openNote` is async (involves IPC to read the file), so `activeNote` hasn't updated yet when `onDeleteNote()` runs. This means it deletes whatever note was *previously* active, not the right-clicked note.  
**Fix:** Pass the file path to the delete handler directly, or await the note open before deleting.  
**Status:** Fixed

## Bug 5 — `listNotes` doesn't skip system directories
**Severity:** High  
**File:** `noted-app/electron/fileService.ts:28-46`  
**Description:** The `walkDir` inside `listNotes()` only skips directories starting with `.`. It walks into `node_modules`, `dist`, `dist-electron`, etc. In contrast, `buildFileTree()` at line 66 explicitly skips these. For a vault rooted at a repo directory, `listNotes` returns hundreds of README.md files from node_modules, which pollute search, graph, and rename-reference-update operations.  
**Fix:** Add the same skip logic from `buildFileTree` to `listNotes`.  
**Status:** Fixed

## Bug 6 — Editor onChange fires on initial load
**Severity:** Medium  
**File:** `noted-app/src/components/Editor.tsx:36-38`  
**Description:** The Milkdown markdown listener fires when the editor initializes with `defaultValueCtx`, triggering `onChange` → `updateContent` → debounced `writeNote` even though the user hasn't edited anything. This causes an unnecessary file write 500ms after opening any note.  
**Fix:** Add a flag to skip the first onChange callback.  
**Status:** Fixed

## Bug 7 — Search does full content scan on every keystroke
**Severity:** Medium  
**File:** `noted-app/src/components/SearchBar.tsx:49-64`  
**Description:** `handleSearch` reads every note's content via IPC on each keystroke with no debouncing. For large vaults this causes lag and excessive IPC calls.  
**Fix:** Add a debounce (200-300ms) before starting the content search.  
**Status:** Fixed

## Bug 8 — Dead code files
**Severity:** Low  
**File:** `noted-app/src/editor/editorSetup.ts`, `noted-app/src/editor/plugins.ts`  
**Description:** These files re-export milkdown presets but are never imported by any component. The Editor component imports directly from `@milkdown/preset-commonmark`.  
**Fix:** Delete both files.  
**Status:** Fixed

## Bug 9 — `git add -A` at repo root is risky
**Severity:** Medium  
**File:** `noted-app/electron/fileService.ts:240`  
**Description:** `gitSync` runs `git add -A` which stages ALL changes in the vault. Since the default vault is the repo root (`Everything_Public`), this stages unrelated files (build artifacts, config changes, etc.) alongside note changes. Combined with auto-commit-and-push, this can push unintended changes.  
**Fix:** Stage only `*.md` files, or add a confirmation step showing what will be committed.  
**Status:** Fixed
