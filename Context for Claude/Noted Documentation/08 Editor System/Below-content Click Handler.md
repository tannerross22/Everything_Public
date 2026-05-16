# Below-content Click Handler

A small UX affordance in [[Editor Component]] that lets the user click in the empty space **below** the last paragraph and start typing there, adding the necessary blank lines automatically.

Without this, ProseMirror only places the cursor where existing content exists — clicking 200 pixels below the last line did nothing.

## Location

The second `useEffect` in [[Editor Component]]:

```ts
useEffect(() => {
  const container = containerRef.current
  if (!container) return

  const handleClick = (e: MouseEvent) => {
    if (!editorInstanceRef.current) return
    try {
      const view = editorInstanceRef.current.ctx.get(editorViewCtx)
      if (!view) return

      const proseMirrorEl = container.querySelector('.ProseMirror') as HTMLElement
      if (!proseMirrorEl) return

      const lastChild = proseMirrorEl.lastElementChild as HTMLElement
      const realContentBottom = lastChild
        ? lastChild.getBoundingClientRect().bottom
        : proseMirrorEl.getBoundingClientRect().bottom

      // Click is within content — let ProseMirror handle it natively
      if (e.clientY <= realContentBottom) return

      // Click is below content — we handle it
      e.preventDefault()

      const gap = e.clientY - realContentBottom
      const linesToAdd = Math.max(1, Math.round(gap / LINE_HEIGHT))

      const { state } = view
      const { tr, schema } = state
      const emptyParagraph = schema.nodes.paragraph.create()
      for (let i = 0; i < linesToAdd; i++) {
        tr.insert(tr.doc.content.size, emptyParagraph)
      }
      const newEnd = tr.doc.content.size
      tr.setSelection(TextSelection.near(tr.doc.resolve(newEnd - 1)))
      view.dispatch(tr)
      view.focus()
    } catch {}
  }

  container.addEventListener('mousedown', handleClick)
  return () => container.removeEventListener('mousedown', handleClick)
}, [noteId])
```

`LINE_HEIGHT = 27` — the rendered line height in CSS (`~1rem × 1.7`). Used to convert pixel gaps into paragraph counts.

## Flow

1. User clicks in the editor container.
2. Compute the bottom edge of the last rendered block (`lastChild.getBoundingClientRect().bottom`).
3. If `clientY <= bottom`, the click is **inside** content — let ProseMirror handle it natively (return without preventing default).
4. Otherwise the click is **below** content:
   - `preventDefault()` to stop ProseMirror's own mousedown handler from grabbing focus elsewhere.
   - Compute `linesToAdd` from the pixel gap.
   - Build a ProseMirror transaction inserting that many empty paragraphs.
   - `TextSelection.near(tr.doc.resolve(newEnd - 1))` places the cursor at the start of the newly inserted text region.
   - Dispatch and focus.

## Why `mousedown` and not `click`

ProseMirror also listens to mousedown. Without `preventDefault()` on `mousedown`, ProseMirror's handler runs first and moves the selection (often to the very last character of the existing content). By the time `click` would fire, the damage is done.

So we listen on `mousedown` and `preventDefault` before ProseMirror sees it.

## Bug history

[[Noted App Bugs|Bug #11]] documented a previous version of this handler that had a `target.closest('.ProseMirror')` guard. Because `.ProseMirror` is the editor container itself, the guard fired on every click and the "below content" logic never ran. Fix:
* Removed the `.closest` guard.
* Added the `clientY <= realContentBottom` check instead.
* Switched from `state.selection.constructor.near` (fragile) to an explicit `TextSelection.near` import.

## Edge cases

* **Empty document.** `lastChild` is null, so `realContentBottom` falls back to the ProseMirror element's own bottom. Click anywhere below it still works (`linesToAdd >= 1`).
* **Editor not mounted.** Defensive `try/catch` swallows errors during the brief window between unmount and effect cleanup.
* **Last child is large (image, table, code block).** `getBoundingClientRect().bottom` gives the visual bottom, so clicking below large blocks works correctly.

## Related

* [[Editor Component]] — where this lives
* [[Milkdown Integration]]
* [[Noted App Bugs]]
