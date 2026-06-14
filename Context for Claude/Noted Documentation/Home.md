# Noted — Documentation Hub

This is the documentation for **Noted**, an Obsidian-like personal knowledge management desktop app built with Electron + React + Milkdown. The documentation is structured so that a fresh reader (or a future AI agent with no prior context) can rebuild a complete mental model of how the application functions, end-to-end.

The app **eats its own dog food**: this documentation is written in the same `.md` files that Noted edits, and every cross-reference uses Noted's `[[wiki-link]]` syntax. Open `Home.md` inside Noted itself to see the graph come alive.

---

## How to navigate this documentation

The folders below are numbered in approximate "depth" order — start at the top for orientation, drill down for detail.

1. **[[About Noted]]** — what the app is and what it does
2. **[[Tech Stack]]** — the libraries and runtimes
3. **[[Project Structure]]** — file layout and where things live
4. **[[Process Model]]** — Electron's main vs. renderer split
5. **[[Data Flow]]** — how an edit propagates from keystroke to disk
6. **[[IPC Layer]]** — the bridge between renderer and main

Every concept links to its neighbors. Click any `[[link]]` to jump.

---

## Sections

### Overview
- [[About Noted]]
- [[Tech Stack]]
- [[Project Structure]]
- [[Quick Start]]
- [[Glossary]]

### Architecture
- [[Process Model]]
- [[IPC Layer]]
- [[Data Flow]]
- [[File Format and Vault]]
- [[Security Model]]

### Electron Main Process
- [[main.ts]]
- [[preload.ts]]
- [[fileService.ts]]
- [[File Watcher]]
- [[Application Menu]]
- [[Window Controls]]
- [[Vault Configuration]]

### File Operations
- [[listNotes]]
- [[buildFileTree]]
- [[readNote and writeNote]]
- [[createNote]]
- [[deleteNote]]
- [[createFolder and deleteFolder]]
- [[moveNote]]
- [[renameNote]]
- [[copyItem]]
- [[Image Pipeline]]

### Git Operations
- [[Git Overview]]
- [[isGitRepo]]
- [[gitStatus]]
- [[gitSync]]
- [[gitLog]]
- [[gitInit]]
- [[gitAddRemote]]
- [[gitGetRemoteUrl]]
- [[gitInitialCommit]]

### Renderer Components
- [[App Component]]
- [[Sidebar Component]]
- [[TabBar Component]]
- [[Editor Component]]
- [[GraphView Component]]
- [[SearchBar Component]]
- [[FindBar Component]]
- [[Modal Component]]
- [[SettingsPage Component]]
- [[Legacy Components]]

### Hooks
- [[useVault]]
- [[useGraph]]
- [[useGitSync]]
- [[useFolderColors]]
- [[useModal]]

### Editor System
- [[Milkdown Integration]]
- [[Wiki Link Plugin]]
- [[Below-content Click Handler]]
- [[Image Handling]]

### Features
- [[Autosave]]
- [[File Watcher Sync]]
- [[Wiki Links]]
- [[Graph View]]
- [[Tabs]]
- [[Multi-Select Deletion]]
- [[Drag and Drop]]
- [[Rename and References]]
- [[Copy and Paste]]
- [[Git Sync]]
- [[Search]]
- [[Find in Note]]
- [[Folder Colors]]
- [[Sidebar Resize and Collapse]]

### Reference
- [[IPC Channels]]
- [[Types]]
- [[Keyboard Shortcuts]]
- [[localStorage Keys]]
- [[Build and Config]]
- [[Custom Title Bar]]

### History
- [[Noted App]] — original design document and phased build plan
- [[Noted App Bugs]] — historical bug tracker
