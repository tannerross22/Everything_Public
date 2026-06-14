# File Format and Vault

Noted is "just files." There is no database, no index, no proprietary format.

## What a note is

A note is a single `.md` file on disk. The **filename** (without `.md`) is the note's display name. Examples:

```
vault/
├── My First Note.md         ←  note named "My First Note"
├── Projects/
│   ├── Apollo.md            ←  note named "Apollo" (in folder "Projects")
│   └── Sketches.md
└── Daily/
    └── 2026-05-15.md
```

There is **no front-matter**. The first line of a freshly created note is `# {name}\n\n` (see [[createNote]]); after that, the file is whatever the user types.

## The vault directory

The "vault" is the root directory Noted recursively scans for `.md` files. It is:

* Configurable per install via `Change Vault` button in the [[Sidebar Component]] footer → `window.api.selectVaultDir()` → native folder picker.
* Persisted to `app.getPath('userData')/noted-config.json` by [[main.ts]]. See [[Vault Configuration]].
* Defaults to the repo root (`Everything_Public`) on a fresh install.

The vault is **the same folder** Noted's source tree lives next to. This is intentional: it means the notes live in the same Git repo as the app, so [[Git Sync]] commits both. See [[Vault Configuration]] for how the default is chosen.

## Folders

Folders are real filesystem directories. Created by [[createFolder]] (`fs.mkdirSync`). The sidebar tree mirrors the file system 1:1 via [[buildFileTree]].

## What gets walked

[[listNotes]] and [[buildFileTree]] both walk recursively, but **skip**:

* Directories whose name starts with `.` (e.g. `.git`, `.vscode`)
* `node_modules`
* `dist`
* `dist-electron`
* `assets` (used by [[Image Pipeline]] for pasted images)

These rules prevent the app from pulling thousands of `README.md` files from `node_modules` into the sidebar and graph (this was [[Noted App Bugs|Bug #5]]).

`listNotes` walks them slightly differently — see the source — but the practical effect is the same.

## Images

Pasted images (or images dropped into the editor) end up in `<vault>/assets/` with hashed filenames like `image-a1b2c3d4.png`. The markdown references them as `![](./assets/image-a1b2c3d4.png)`. See [[Image Pipeline]] for the full flow.

## Wiki links

`[[Note Name]]` references inside any note's body are parsed at runtime by [[useGraph]] (for the graph) and [[Wiki Link Plugin]] (for in-editor styling and click handling). They are stored **verbatim** in the markdown — Noted does not transform them on save. This means GitHub renders them as literal `[[Note Name]]` text in its UI; Noted is the only place that resolves them.

## Git layout

If the vault is also a git working tree (it is, by default), then on each [[Git Sync]] every modified file is staged with `git add -A`. Because the vault root may contain non-note files (the app source, build artifacts, etc.), this stages **everything** — see [[Noted App Bugs|Bug #9]]. The user is responsible for `.gitignore`'ing artifacts they don't want pushed.

## File modification time

The sidebar uses `fs.statSync(filePath).mtimeMs` (in [[listNotes]] and [[buildFileTree]]) as the note's `modifiedAt`. Displayed under each filename in the [[Sidebar Component]], and used for the modified-time sort orders (see [[Keyboard Shortcuts]] → File menu → Sort).

## Path encoding

* On Windows paths use `\` separators; on macOS/Linux `/`. The codebase does both by detecting at runtime (`includes('\\')`).
* `pathJoin(parent, name)` in [[Sidebar Component]] picks the separator based on parent.
* Image paths in markdown always use forward slashes for cross-platform compatibility (`./assets/image-…`).

## Related

* [[Vault Configuration]] — how the vault path is persisted
* [[listNotes]], [[buildFileTree]] — how the vault is read
* [[File Watcher]] — how external changes are detected
* [[Wiki Links]]
* [[Image Pipeline]]
