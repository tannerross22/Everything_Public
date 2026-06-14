# Milkdown Integration

How Noted uses Milkdown (a ProseMirror-based WYSIWYG markdown editor). Architecture-level — for the component code itself see [[Editor Component]]; for the wiki-link plugin see [[Wiki Link Plugin]].

## Why Milkdown?

Three features Noted needs:

1. **Inline rendering.** As the user types `## Heading`, the editor immediately renders that line as an `<h2>` — no separate preview pane. This is WYSIWYG-style markdown editing.
2. **Plain markdown round-trip.** What gets saved to disk is the same markdown a human (or Claude Code, or VS Code) would write. No proprietary "rich" format.
3. **Plugin system.** ProseMirror is well-known and Milkdown exposes it cleanly. Custom decorations like [[Wiki Link Plugin]] are straightforward.

Other candidates considered (per the original [[Noted App]] design doc):
* TipTap — also ProseMirror-based, similar capabilities, no decisive advantage.
* CodeMirror — text-mode editor with split preview, not WYSIWYG.

## Packages in use

| Package | Role |
|---|---|
| `@milkdown/core` | Editor factory, plugin/Ctx system |
| `@milkdown/ctx` | Ctx primitives (used transitively) |
| `@milkdown/preset-commonmark` | Parse/serialize CommonMark |
| `@milkdown/preset-gfm` | GFM extras (tables, strikethrough, task lists) |
| `@milkdown/plugin-history` | Undo/redo |
| `@milkdown/plugin-listener` | Hooks into `markdownUpdated` and `docChanged` |
| `@milkdown/plugin-trailing` | (installed but not enabled) trailing-paragraph plugin |
| `@milkdown/plugin-upload` | (installed but not enabled) image upload plugin |
| `@milkdown/theme-nord` | Base theme (Catppuccin-ish dark via CSS overrides) |
| `@milkdown/prose` | ProseMirror primitives — used by the custom plugin |
| `@milkdown/utils` | The `$prose` helper for plugin authoring |

## Editor factory pattern

```ts
const editor = await MilkdownEditor.make()
  .config(nord)
  .config(ctx => {
    ctx.set(rootCtx, element)
    ctx.set(defaultValueCtx, initialMarkdown)
  })
  .use(commonmark)
  .use(gfm)
  .use(history)
  .use(listener)
  .config(ctx => {
    ctx.get(listenerCtx).markdownUpdated(callback)
  })
  .use(createWikiLinkPlugin(onLinkClick))
  .create()
```

Builder pattern: each `.use(...)` and `.config(...)` registers a contribution, `.create()` materializes the editor.

The **Ctx system** is Milkdown's dependency-injection container. `ctx.set(rootCtx, ...)` tells the editor where to mount; `ctx.get(listenerCtx)` retrieves the listener API to subscribe to update events.

## What goes through the listener

`markdownUpdated((ctx, markdown, prevMarkdown) => …)` fires on every doc change. Noted's callback (in [[Editor Component]]):

1. Skips the first invocation (the one at mount with `defaultValueCtx`) via `initialLoadRef`. (See [[Noted App Bugs|Bug #6]].)
2. Checks for `data:image` substrings and routes through [[Image Pipeline]] if present.
3. Calls `onChange(markdown)` which is `updateContent` from [[useVault]].

## Remount-on-switch instead of imperative update

When the user switches notes, [[App Component]] passes a new `noteId` prop. Because [[Editor Component]] uses `key={activeNote.path}`, React fully unmounts the old editor and mounts a new one with the new content.

The alternative — imperatively replacing the document — was rejected for three reasons:

* **Cursor and selection bugs.** ProseMirror's `replaceWith` resets selection in subtle ways.
* **Undo history pollution.** A "replace everything" transaction is recorded in history, so Ctrl+Z would bring back the previous note's content.
* **Decoration recompute timing.** The [[Wiki Link Plugin]] reads the new doc on `tr.docChanged`; an imperative replace would trigger it once per character of difference.

The remount cost is ~50ms — imperceptible to the user.

## Theme

The base theme is `nord`. Most of the styling actually comes from `src/App.css` which overrides Nord's CSS variables to match the Catppuccin Mocha palette used elsewhere in the app:

```css
.milkdown {
  --crepe-color-surface: var(--bg-primary);
  --crepe-color-on-surface: var(--text-primary);
  /* ... */
}
```

And the `.ProseMirror` selector is heavily styled (font, line-height, heading sizes, list bullets, code blocks).

## The Ctx pattern in `createWikiLinkPlugin`

Plugins built via `$prose(() => new Plugin(…))` from `@milkdown/utils` get automatic integration with Milkdown's Ctx system. The plugin receives the Ctx but doesn't need anything from it — it operates purely on ProseMirror state.

See [[Wiki Link Plugin]] for the full plugin implementation.

## Limitations and known gaps

* **External edits don't refresh the open note.** Milkdown reads `defaultValueCtx` at mount only. If the same note is edited externally while open, the editor's view doesn't update until the user switches tabs and back. The renderer's `activeNote.content` state does update — there's just no observer wiring it back into ProseMirror. See [[File Watcher]] and [[useVault]].
* **No markdown source view.** No way to view/edit the raw `[[link]]` brackets — the [[Wiki Link Plugin]] decoration is always applied. Users have to look at the file outside Noted to see the raw markdown.
* **No image uploads from drag-drop.** `@milkdown/plugin-upload` is installed but not enabled. Paste-image works through [[Image Pipeline]].

## Related

* [[Editor Component]] — the React wrapper
* [[Wiki Link Plugin]] — the custom decoration plugin
* [[Image Pipeline]] — the base64-to-file path
* [[Below-content Click Handler]] — the click-empty-space affordance
* [[Tech Stack]]
