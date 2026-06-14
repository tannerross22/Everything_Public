# Image Pipeline

How pasted/dropped images become files in `<vault>/assets/` and references in markdown.

## Two entry points

### 1. Direct image upload — `saveImage`

**Source:** `electron/fileService.ts` → `saveImage(vaultDir, buffer, type)`
**IPC channel:** `vault:saveImage`
**Renderer access:** `window.api.saveImage(vaultDir, arrayBuffer, type)`

```ts
export function saveImage(vaultDir: string, imageBuffer: Buffer, imageType: string): string {
  const assetsDir = path.join(vaultDir, 'assets')
  if (!fs.existsSync(assetsDir)) fs.mkdirSync(assetsDir, { recursive: true })

  const timestamp = Date.now()
  const extension = imageType === 'image/png' ? 'png' :
                    imageType === 'image/jpeg' ? 'jpg' : 'webp'
  const filename = `image-${timestamp}.${extension}`
  const filepath = path.join(assetsDir, filename)

  fs.writeFileSync(filepath, imageBuffer)
  return `./assets/${filename}`     // forward-slash path for markdown
}
```

* The IPC handler in [[main.ts]] receives the data as `ArrayBuffer`, wraps it in `Buffer.from(arrayBuffer)`, then delegates here.
* Filename is timestamp-based — collisions are unlikely but possible within the same millisecond. Not currently guarded.
* Returns a **forward-slash** path (`./assets/...`) so it works in markdown on both Windows and Unix.

This entry point is **available but not currently wired in the editor.** It exists for a future drag-and-drop image upload feature. The current flow uses path 2.

### 2. Base64 → file — `convertBase64ImagesToFiles`

**Source:** `electron/fileService.ts` → `convertBase64ImagesToFiles(vaultDir, noteId, markdown)`
**IPC channel:** `vault:convertBase64ImagesToFiles`
**Renderer access:** `window.api.convertBase64ImagesToFiles(vaultDir, noteId, markdown)`

When the user pastes an image, Milkdown (more specifically its CommonMark serializer) inlines it as a base64 data URL:

```markdown
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA…)
```

This works but bloats the markdown file and is unreadable in any text editor. `convertBase64ImagesToFiles` scans the markdown, writes each base64 blob to a file in `assets/`, and replaces the data URL with a file reference:

```ts
const base64ImageRegex = /!\[\]\(data:image\/(\w+);base64,([A-Za-z0-9+/=]+)\)/g

for (const match of markdown.matchAll(base64ImageRegex)) {
  const imageType = match[1]                     // png, jpeg, webp, …
  const base64Data = match[2]

  // Content-hash the base64 data → reproducible filename
  const crypto = require('crypto')
  const hash = crypto.createHash('md5').update(base64Data).digest('hex').substring(0, 8)
  const extension = imageType === 'jpeg' ? 'jpg' : imageType
  const filename = `image-${hash}.${extension}`
  const filepath = path.join(assetsDir, filename)

  if (!fs.existsSync(filepath)) {
    fs.writeFileSync(filepath, Buffer.from(base64Data, 'base64'))
  }
  updatedMarkdown = updatedMarkdown.replace(fullMatch, `![](./assets/${filename})`)
}
```

The **content-hash filename** means the same image always gets the same filename — pasting the same screenshot twice produces one file, two references.

## When it runs

In [[Editor Component]], on every `markdownUpdated`:

```ts
ctx.get(listenerCtx).markdownUpdated((_ctx, markdown) => {
  if (initialLoadRef.current) { initialLoadRef.current = false; return }
  if (vaultDir && markdown.includes('data:image')) {
    window.api.convertBase64ImagesToFiles(vaultDir, noteId, markdown).then(updatedMarkdown => {
      onChange(updatedMarkdown)   // pass the converted markdown to useVault
    }).catch(() => {
      onChange(markdown)
    })
  } else {
    onChange(markdown)
  }
})
```

The renderer fast-path `markdown.includes('data:image')` avoids the IPC roundtrip when there's nothing to convert. If conversion fails, the original (base64) markdown is saved — better to have bloat than data loss.

The converted markdown is the version actually written to disk. Within a few hundred milliseconds of pasting an image, the `.md` file contains `![](./assets/image-abc12345.png)` rather than the base64 blob.

## The `assets/` directory

* Lives at `<vault>/assets/`.
* Excluded from [[buildFileTree]] (no clutter in the sidebar).
* Excluded from [[listNotes]] (no clutter in search/graph).
* Included in the [[File Watcher]] glob (`**/*.md`) only by accident — there are no `.md` files in `assets/`.
* Tracked by git like everything else; `git add -A` in [[gitSync]] commits new images.

## Bugs avoided

* **No infinite loop.** The `initialLoadRef` guard in [[Editor Component]] ensures the conversion doesn't trigger on first mount. ([[Noted App Bugs|Bug #6]] was the related save-on-load issue.)
* **No duplicate files.** Content-hashing ensures the same image is stored once.

## Limitations

* **Only handles `![](data:image/…)`.** If a user pastes HTML or a markdown image with alt text (`![alt](…)`), the regex misses it.
* **Loses alt text.** All converted images get empty alt `![]()`. Future improvement.
* **No image preview in sidebar.** Sidebar only shows `.md` files.

## Related

* [[Editor Component]] — calls the conversion on every markdown update
* [[fileService.ts]]
* [[File Format and Vault]] — directory layout
