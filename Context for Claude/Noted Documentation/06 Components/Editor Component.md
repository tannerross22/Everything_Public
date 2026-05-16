# Editor Component

**Path:** `src/components/Editor.tsx`

Wraps Milkdown (a ProseMirror-based WYSIWYG markdown editor). Responsible for: instantiating the editor, wiring the markdown-update listener, mounting the [[Wiki Link Plugin]], and handling the "click below content" affordance.

The full Milkdown setup is also covered in [[Milkdown Integration]] (architecture-level) and [[Wiki Link Plugin]] (the custom plugin). This page is about the React-side wrapper.

## Props

```ts
interface EditorProps {
  content: string        // initial markdown (also used as the only mount-time value)
  onChange: (markdown: string) => void
  noteId: string         // typically the note path; used as React key
  onLinkClick?: (target: string) => void
  vaultDir?: string      // for the base64 → file image conversion
}
```

## Key insight: remount on note switch

```tsx
<Editor key={activeNote.path} content={activeNote.content} … />
```

The `key={activeNote.path}` in [[App Component]] forces a **full unmount and remount** every time a different note is opened. We could have switched content imperatively (`view.dispatch(replaceAll(newDoc))`), but remounting is simpler and avoids subtle ProseMirror state bugs (cursor position, undo history, decorations).

This is a deliberate architectural decision — see [[Noted App|Phase 3]] in the original design doc.

## Mount lifecycle

```ts
useEffect(() => {
  if (!editorRef.current) return
  initialLoadRef.current = true

  const createEditor = async () => {
    const editor = await MilkdownEditor.make()
      .config(nord)                    // base theme
      .config(ctx => {
        ctx.set(rootCtx, el)            // attach to our <div>
        ctx.set(defaultValueCtx, content)
      })
      .use(commonmark)                  // CommonMark parse/serialize
      .use(gfm)                         // GFM extras (tables, strikethrough, task lists)
      .use(history)                     // Undo/redo (Ctrl+Z / Ctrl+Shift+Z)
      .use(listener)                    // markdownUpdated callback
      .config(ctx => {
        ctx.get(listenerCtx).markdownUpdated((_ctx, markdown) => {
          if (initialLoadRef.current) { initialLoadRef.current = false; return }
          // …handle save (see below)…
        })
      })
      .use(onLinkClick ? createWikiLinkPlugin(onLinkClick) : [])
      .create()

    editorInstanceRef.current = editor
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        editor.ctx.get(editorViewCtx)?.dom.focus()
      })
    })
  }

  createEditor()
  return () => {
    editorInstanceRef.current?.destroy()
    editorInstanceRef.current = null
  }
}, [noteId])
```

### The double `requestAnimationFrame`

After mount, we focus the editor. The double rAF gives Milkdown two paint frames to finish laying out before we steal focus — without it the focus call sometimes raced ProseMirror's own setup and silently no-op'd.

### The `initialLoadRef` gate

The Milkdown `markdownUpdated` listener fires **once on mount** with the initial content, which would trigger an autosave even though the user hasn't typed. The `initialLoadRef.current` flag skips the first call.

This was [[Noted App Bugs|Bug #6]].

## Save / base64-conversion flow

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

* The fast-path `markdown.includes('data:image')` skips the IPC roundtrip when there's nothing to convert.
* On error, the original markdown is passed through — we prefer "saved with bloat" over "data lost."
* `onChange` is `updateContent` from [[useVault]], which debounces 100ms before writing.

See [[Image Pipeline]] for what `convertBase64ImagesToFiles` does.

## Click-below-content handler

A second `useEffect` adds a `mousedown` listener on the container that lets the user click in the empty space below the document to insert empty paragraphs and place the cursor there:

```ts
const lastChild = proseMirrorEl.lastElementChild as HTMLElement
const realContentBottom = lastChild ? lastChild.getBoundingClientRect().bottom : proseMirrorEl.getBoundingClientRect().bottom

// Click is within content → let ProseMirror handle it natively
if (e.clientY <= realContentBottom) return

// Click is below content → we handle it
e.preventDefault()
const gap = e.clientY - realContentBottom
const linesToAdd = Math.max(1, Math.round(gap / LINE_HEIGHT))    // LINE_HEIGHT = 27

const { state } = view
const { tr, schema } = state
const emptyParagraph = schema.nodes.paragraph.create()
for (let i = 0; i < linesToAdd; i++) {
  tr.insert(tr.doc.content.size, emptyParagraph)
}
tr.setSelection(TextSelection.near(tr.doc.resolve(tr.doc.content.size - 1)))
view.dispatch(tr)
view.focus()
```

This makes the editor feel "full canvas" — Obsidian and similar apps do the same. Without it, the user can only place their cursor where existing content exists.

This was [[Noted App Bugs|Bug #11]] — the original handler had a `.closest('.ProseMirror')` guard that never let the below-content branch fire. Detail in [[Below-content Click Handler]].

## What Editor doesn't do

* It doesn't handle the wiki-link click decoration — that's the [[Wiki Link Plugin]].
* It doesn't autosave directly — it passes markdown to `onChange` and lets [[useVault]] debounce.
* It doesn't render images itself — Milkdown's built-in image node handles `![](...)`.

## Related

* [[Milkdown Integration]] — architectural overview
* [[Wiki Link Plugin]]
* [[Below-content Click Handler]]
* [[Image Pipeline]]
* [[useVault]]
* [[Autosave]]
