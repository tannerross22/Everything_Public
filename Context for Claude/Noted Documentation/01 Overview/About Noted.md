# About Noted

Noted is a desktop knowledge-management app modeled after Obsidian. It is built on Electron with a React renderer, uses Milkdown (a ProseMirror-based WYSIWYG markdown editor), and stores every note as a plain `.md` file on disk.

## Goals

1. **Plain files, always.** Notes are flat `.md` files in a "vault" directory. No proprietary format, no database. Any external editor (VS Code, vim, Claude Code, GitHub web) edits the same files transparently.
2. **Inline markdown rendering.** While the user types `## Heading`, the editor renders that as a heading immediately — no separate preview pane. See [[Milkdown Integration]].
3. **Linked notes.** `[[Note Name]]` syntax inside any note creates a hyperlink to another note. Clicking the link opens it (creating it first if absent). See [[Wiki Links]].
4. **Graph visualization.** All `[[links]]` are parsed into a force-directed graph showing the structure of the vault. See [[Graph View]].
5. **GitHub sync.** One button stages, commits, pulls, and pushes the entire vault via `git`. See [[Git Sync]].
6. **Live external edits.** A file-system watcher detects external changes to notes and refreshes the sidebar/editor automatically. See [[File Watcher]].

## What Noted is not

* It is **not** a multi-user system. There is no server, no auth, no real-time collaboration. Sync is via Git, as a flat-file pull/push.
* It is **not** a publishing platform. The renderer is the only viewer.
* It is **not** a database. There is no index file, no metadata sidecar. Note relationships are computed at runtime by scanning every `.md` for `[[links]]`.

## Default vault

By default the vault is the parent directory of the `noted-app/` folder — i.e. the `Everything_Public` repository. See [[Vault Configuration]] for how this is persisted and changed at runtime, and [[File Format and Vault]] for the on-disk layout.

## Related

* [[Tech Stack]] — every library Noted depends on
* [[Project Structure]] — where each piece of code lives
* [[Process Model]] — the Electron split between [[main.ts]] and the React renderer
