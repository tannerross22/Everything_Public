# createNote

**Source:** `electron/fileService.ts` → `createNote(vaultDir, name)`
**IPC channel:** `vault:create`
**Renderer access:** `window.api.createNote(vaultDir, name)`

## Signature

```ts
function createNote(vaultDir: string, name: string): string  // returns the new path
```

## What it does

Creates a new `.md` file in `vaultDir` named `${name}.md`, with stock initial content `# {name}\n\n`. **Handles name collisions** by appending ` 1`, ` 2`, … until a free filename is found.

```ts
let fileName = `${name}.md`
let fullPath = path.join(vaultDir, fileName)
let counter = 1
while (fs.existsSync(fullPath)) {
  fileName = `${name} ${counter}.md`
  fullPath = path.join(vaultDir, fileName)
  counter++
}
fs.writeFileSync(fullPath, `# ${name}\n\n`, 'utf-8')
return fullPath
```

The collision counter is what produces filenames like `Untitled.md`, `Untitled 1.md`, `Untitled 2.md`.

## The "vaultDir" parameter is actually any folder

Misleadingly named: this argument is just the **target directory**. [[useVault]] `createNewNote` passes either `vaultDir` (for root-level creation) or a subfolder path:

```ts
const createNewNote = async (name: string, folderPath?: string) => {
  if (!vaultDir || !name.trim()) return undefined
  const targetDir = folderPath ?? vaultDir
  const filePath = await window.api.createNote(targetDir, name.trim())
  await refreshNotes()
  return filePath
}
```

So a user creating "Apollo" inside the `Projects` folder ends up calling `createNote('C:/.../Projects', 'Apollo')`.

## The watcher guard

The IPC handler in [[main.ts]]:

```ts
ipcMain.handle('vault:create', (_event, vaultDir, name) => {
  isWriting = true
  const result = createNote(vaultDir, name)
  setTimeout(() => { isWriting = false }, 200)
  return result
})
```

Same self-write guard pattern as [[readNote and writeNote|writeNote]] — suppresses one chokidar event so the renderer doesn't refresh twice. Unlike `vault:write`, this handler does **not** manually fire `vault:files-changed`; the chokidar event after the guard expires will do it.

## Callers in the renderer

| Caller | Triggered by |
|---|---|
| [[useVault]] `createNewNote` | Sidebar "+ note" buttons, Ctrl+N, [[Wiki Links]] resolution to a missing note |
| [[App Component]] `handleGitSetup` | Indirect — via [[gitInitialCommit]] |

## Wiki-link integration

When the user clicks a `[[Foo]]` link and `Foo.md` doesn't exist, [[App Component]]'s `resolveLink` calls `createNewNote(linkName, targetFolder)` where `targetFolder` is the folder of the currently active note (or vault root). The new note then opens in a tab via `openNoteInTab`.

## Initial content

The body is just `# {name}\n\n`. Two newlines so the user's cursor lands on a blank line below the heading after the editor mounts.

There is no front-matter, tag, or date inserted. Adding "automatic" front-matter is a frequently requested feature; it would be done here.

## Related

* [[useVault]] `createNewNote`
* [[Wiki Links]] — auto-create on click
* [[Sidebar Component]] — inline create input
* [[App Component]] — Ctrl+N keyboard handler, prompt modal
* [[readNote and writeNote|writeNote]] — the underlying write
