# Data Flow

This page traces three common user actions end-to-end. Each trace names every file, function, and IPC channel involved.

## Trace 1 — User types in the editor

```
1. Keystroke in [[Editor Component]] (Milkdown / ProseMirror)
       │
       ▼
2. Milkdown plugin-listener fires markdownUpdated(_, markdown)
   inside Editor.tsx → ctx.get(listenerCtx)
       │
       ▼
3. Editor's initialLoadRef gate: skip if first call (avoids spurious save on load)
       │
       ▼
4. If markdown contains 'data:image' → window.api.convertBase64ImagesToFiles(…)
   (see [[Image Pipeline]])
       │
       ▼
5. onChange(markdown) → which is updateContent from [[useVault]]
       │
       ▼
6. updateContent: setActiveNote({…, content}); saveNote(path, content)
       │
       ▼
7. saveNote debounces 100ms (saveTimerRef) then:
       window.api.writeNote(filePath, content)
       │
       ▼
8. IPC: 'vault:write' → main.ts handler
   • isWriting = true (suppress file watcher)
   • writeNote(filePath, content) [[writeNote]] → fs.writeFileSync
   • setTimeout 200ms: isWriting = false
   • mainWindow.webContents.send('vault:files-changed')
       │
       ▼
9. [[useVault]] onFilesChanged callback runs:
   • refreshNotes() → window.api.listNotes + buildFileTree
   • Re-reads active note content if open
       │
       ▼
10. Sidebar re-renders (new fileTree); Editor stays mounted (content prop unchanged in value)
```

**Why the 100ms debounce in [[useVault]]?** To coalesce rapid keystrokes into one write. Originally 500ms; tightened to 100ms because users perceived the delay as data loss when closing quickly.

**Why also a 200ms guard in main?** The watcher's `awaitWriteFinish: 300` plus our 200ms guard together make sure the post-write `files-changed` event we send is the one the renderer sees, not the one chokidar would have raised.

## Trace 2 — User clicks a `[[wiki link]]` inside a note

```
1. Click on a span with class .wiki-link
       │
       ▼
2. ProseMirror Plugin.props.handleClick (in [[Wiki Link Plugin]])
   • target.closest('.wiki-link')
   • Reads data-target attribute
   • Calls onLinkClick(linkTarget)
       │
       ▼
3. onLinkClick = onLinkClick prop from [[Editor Component]],
   which is set in [[App Component]] to:
       (linkName) => resolveLink(linkName).then(path => openNoteInTab(path))
       │
       ▼
4. resolveLink in [[App Component]] (overrides the one from useVault to use modal.confirm):
   • Searches notes[] for case-insensitive name match
       • Found → await openNote(match.path); return path
       • Not found → modal.confirm 'Create new note "{name}"?'
                       → createNewNote(name, targetFolder)
                       → openNote(newPath); return newPath
       │
       ▼
5. openNoteInTab(path) in [[App Component]]:
   • await openNote(path)        // useVault loads content
   • setOpenTabs / setActiveTabIndex   // adds tab if not present
   • setViewMode('editor')
       │
       ▼
6. [[Editor Component]] receives new noteId (= path); key={path} forces remount
```

## Trace 3 — User edits the file outside Noted

```
1. External save (VS Code, Claude Code, vim) → fs.writeFile on a vault .md
       │
       ▼
2. chokidar watcher (started in [[main.ts]] startWatcher) fires 'all' event
   after awaitWriteFinish (300ms stability)
       │
       ▼
3. Handler in main.ts:
   if (!isWriting && mainWindow) mainWindow.webContents.send('vault:files-changed')
       │  (isWriting = false because we didn't initiate this write)
       ▼
4. Renderer side: every subscriber to window.api.onFilesChanged receives the event:
   • [[useVault]] → refreshNotes() + re-read activeNote content
   • [[useGitSync]] → setIsProcessing(true), debounce 1s, then refreshGitStatus()
   • Anyone else (currently nobody else subscribes)
       │
       ▼
5. [[Sidebar Component]] re-renders with new file tree
   [[Editor Component]] does NOT remount (noteId hasn't changed) — instead, content
   prop updates, but ProseMirror is uncontrolled, so the visible doc won't change.

   ⚠ Caveat: if the user has the same note open and edits externally, the editor
     will be stale until they switch tabs back (the activeNote.content state
     updates, but Milkdown only reads defaultValueCtx on mount).
```

## Trace 4 — User clicks Sync button

```
1. .rail-sync-btn (App.tsx) or .sync-btn (Sidebar.tsx) onClick → gitSync.handleSync
   (both call the same function from [[useGitSync]])
       │
       ▼
2. handleSync in useGitSync:
   • setSyncing(true)
   • timestamp = 'YYYY-MM-DD HH:MM:SS'
   • await window.api.gitSync(vaultDir, `vault sync: ${timestamp}`)
       │
       ▼
3. IPC 'git:sync' → main.ts handler → [[gitSync]] in fileService.ts:
   git add -A  →  git commit -m  →  git fetch origin
   → if detached HEAD: detect 'master' or 'main' and checkout
   → git pull origin <branch> --allow-unrelated-histories -X ours
   → git push -u origin <branch> -v
       │
       ▼
4. After gitSync resolves, main.ts emits 'vault:files-changed' (so any new files from
   the pull show up in the sidebar)
       │
       ▼
5. useGitSync:
   • 500ms wait, then refreshGitStatus()
   • showSynced = true (briefly flash a "Synced" state in the UI)
   • setTimeout(2000) → showSynced = false
   • setSyncing(false)
```

## Cross-cutting: what triggers `vault:files-changed`

Every place the watcher fires that event:

* Any external `.md` change detected by chokidar.
* After every write via [[main.ts]] handlers (`vault:write`, `vault:create`, `vault:delete`, `vault:deleteFolder`, etc.).
* After `git:sync` completes (so pulled changes appear).

The renderer treats every fire identically: just refresh.

## Related

* [[Process Model]]
* [[IPC Layer]]
* [[useVault]]
* [[Autosave]]
