# Image Handling

This is the **renderer-side** view of how images move from user paste → saved file. The main-process worker functions are documented in [[Image Pipeline]].

## End-to-end

1. **User pastes** an image into the editor (Ctrl+V over Milkdown).
2. Milkdown's commonmark serializer inlines the image as a **base64 data URL**:
   ```markdown
   ![](data:image/png;base64,iVBORw0KGgo…)
   ```
3. The Milkdown `listenerCtx.markdownUpdated` callback fires with the new markdown (which contains the base64 blob).
4. [[Editor Component]] detects `data:image` in the markdown and routes through [[convertBase64ImagesToFiles|main]]:
   ```ts
   if (vaultDir && markdown.includes('data:image')) {
     window.api.convertBase64ImagesToFiles(vaultDir, noteId, markdown).then(updatedMarkdown => {
       if (updatedMarkdown !== markdown) onChange(updatedMarkdown)
       else onChange(markdown)
     }).catch(() => onChange(markdown))
   } else {
     onChange(markdown)
   }
   ```
5. Main process scans the markdown, writes each base64 image as a file under `<vault>/assets/image-{hash}.{ext}`, replaces the data URL with `![](./assets/image-{hash}.{ext})`, returns the updated markdown.
6. The updated markdown — now small and human-readable — is passed to `onChange`, which goes through [[useVault]]'s autosave to disk.

Within a few hundred milliseconds of the paste, the `.md` file contains a file reference instead of a multi-megabyte base64 string.

## Why this design

Milkdown gives us base64 markdown out of the box for free. We could intercept the paste event in ProseMirror and convert at paste time, but:

* Hooking ProseMirror's paste handler is fragile — many ways to insert content.
* The markdown-level conversion is **deterministic** — same image → same hash → same filename, regardless of how the image got into the document.
* It works for images that arrive **without** being pasted (e.g. another app modifies the markdown to embed base64).

## Content-hashed filenames

```ts
const hash = crypto.createHash('md5').update(base64Data).digest('hex').substring(0, 8)
const filename = `image-${hash}.${extension}`
```

The 8-char MD5 prefix of the base64 string. Two consequences:

1. **Same image = same file.** Paste the same screenshot twice → one file on disk, two `![]()` references in the markdown.
2. **Files are stable across edits.** Renaming the note or moving it doesn't affect the image filenames.

## Fast-path

The renderer-side `markdown.includes('data:image')` check skips the IPC roundtrip when there's nothing to convert. Vast majority of edits don't touch images, so this avoids hundreds of unnecessary IPC calls per minute.

## What happens on conversion failure

```ts
.catch(() => onChange(markdown))
```

If `convertBase64ImagesToFiles` rejects (disk full, permission error, etc.), the original markdown is saved instead. We choose **"saved with bloat"** over **"data lost."** The next save attempt will retry the conversion.

## Limitations

* **Only handles `![](data:image/…)` exactly.** Alt text breaks the regex: `![Screenshot](data:…)` won't be converted. (Milkdown by default produces empty alt for pasted images, so this is rare.)
* **All converted images lose alt text.** Even if the source had alt text, the replacement is `![](./assets/…)`. Future improvement.
* **No drag-and-drop image upload.** Milkdown's `@milkdown/plugin-upload` is installed but not enabled. To enable, configure the plugin's uploader to call `window.api.saveImage` (from [[saveImage|saveImage]]).
* **`assets/` is shared across notes.** No per-note image folders. This is intentional (deduplication via content hash) but means if a note is deleted, its images stay around — there's no GC.

## Related

* [[Image Pipeline]] — main-process functions
* [[Editor Component]] — where the markdown is intercepted
* [[saveImage]] — direct upload function (unused but available)
* [[convertBase64ImagesToFiles]] — the conversion function
