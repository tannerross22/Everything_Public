# Wiki Link Plugin

**Path:** `src/editor/wikiLinkPlugin.ts`

A custom ProseMirror plugin that gives `[[wiki links]]` their styled appearance and click behavior, without touching the markdown source.

## Why "decoration" not "mark"?

There are two ways to add styling to text in ProseMirror:

| Approach | Markdown impact | Complexity |
|---|---|---|
| **Mark** — a real schema element wrapping the text | Requires custom parse + serialize rules so the `[[…]]` syntax round-trips | ~300 lines, lots of edge cases |
| **Decoration** — a visual overlay applied on top of plain text | None — the markdown stays as literal `[[Foo]]` | ~80 lines |

Decorations don't change the document — they're just CSS overlays. ProseMirror handles them entirely in the **view layer**. Round-tripping is trivial: the raw `[[Foo]]` text is what gets serialized to disk and re-parsed on next load.

This was a deliberate architectural decision in the original [[Noted App|Phase 4]] design.

## The full plugin

```ts
import { $prose } from '@milkdown/utils'
import { Plugin, PluginKey } from '@milkdown/prose/state'
import { Decoration, DecorationSet } from '@milkdown/prose/view'
import type { Node } from '@milkdown/prose/model'

const wikiLinkPluginKey = new PluginKey('wikiLink')

export function createWikiLinkPlugin(onLinkClick: (target: string) => void) {
  return $prose(() => {
    return new Plugin({
      key: wikiLinkPluginKey,
      state: {
        init(_, state) { return findWikiLinks(state.doc) },
        apply(tr, oldDecorations) {
          if (tr.docChanged) return findWikiLinks(tr.doc)
          return oldDecorations
        },
      },
      props: {
        decorations(state) { return this.getState(state) },
        handleClick(_view, _pos, event) {
          const target = event.target as HTMLElement
          const linkEl = target.closest('.wiki-link')
          if (linkEl) {
            const linkTarget = linkEl.getAttribute('data-target')
            if (linkTarget) { onLinkClick(linkTarget); return true }
          }
          return false
        },
      },
    })
  })
}

function findWikiLinks(doc: Node): DecorationSet {
  const decorations: Decoration[] = []
  doc.descendants((node, pos) => {
    if (!node.isText || !node.text) return
    const regex = /\[\[([^\]]+)\]\]/g
    let match
    while ((match = regex.exec(node.text)) !== null) {
      const start = pos + match.index
      const end = start + match[0].length
      const linkTarget = match[1]
      decorations.push(
        Decoration.inline(start, end, {
          class: 'wiki-link',
          'data-target': linkTarget,
          nodeName: 'span',
        })
      )
    }
  })
  return DecorationSet.create(doc, decorations)
}
```

## How it's wired into the editor

[[Editor Component]] adds the plugin via `.use(...)`:

```ts
.use(onLinkClick ? createWikiLinkPlugin(onLinkClick) : [])
```

The `onLinkClick` callback comes from [[App Component]] and routes:

```
linkName → resolveLink(linkName) → openNoteInTab(path)
```

See [[Wiki Links]] for the full flow.

## The two pieces

### 1. The state — `findWikiLinks(doc)`

ProseMirror plugins can have a "state" that gets recomputed via `apply(tr, oldState)`. Here the state is a `DecorationSet`.

```ts
state: {
  init(_, state) { return findWikiLinks(state.doc) },
  apply(tr, oldDecorations) {
    if (tr.docChanged) return findWikiLinks(tr.doc)
    return oldDecorations
  },
}
```

* **On mount:** scan the document for `[[...]]` patterns; build decorations.
* **On every transaction:** if the doc changed, rescan; otherwise reuse the cached decoration set.

The scan walks `doc.descendants` and applies `Decoration.inline(start, end, attrs)` to each `[[…]]` range. The attrs include a `class` for styling and a `data-target` for the click handler.

### 2. The props — `decorations` and `handleClick`

```ts
props: {
  decorations(state) { return this.getState(state) },
  handleClick(_view, _pos, event) {
    const linkEl = (event.target as HTMLElement).closest('.wiki-link')
    if (linkEl) {
      const linkTarget = linkEl.getAttribute('data-target')
      if (linkTarget) { onLinkClick(linkTarget); return true }
    }
    return false
  },
}
```

* `decorations` returns the cached DecorationSet — ProseMirror applies these in the DOM as wrapping `<span class="wiki-link" data-target="…">` elements.
* `handleClick` checks if the click target is inside a `.wiki-link` span; if so, extracts the target and calls the consumer's callback. Returning `true` stops ProseMirror's default click handling.

## Styling

In `src/App.css`:

```css
.wiki-link {
  color: var(--accent);                       /* purple */
  text-decoration: underline dotted;
  cursor: pointer;
  font-weight: 500;
}

.wiki-link:hover {
  background: rgba(203, 166, 247, 0.15);
  border-radius: 3px;
}
```

The dotted underline distinguishes a wiki link from a regular link (solid underline). Purple matches the app's accent color.

## Edge cases

* **Empty links:** `[[]]` doesn't match because `[^\]]+` requires one or more non-`]` characters.
* **Nested brackets:** `[[outer [[inner]] ]]` — the regex is greedy until the first `]]`, so it captures `outer [[inner` and treats `]]` as the closing. The "innermost" pair effectively wins. Not common in practice.
* **Single-bracket** `[link]` — ignored.
* **Cross-paragraph spans** — ProseMirror text nodes don't cross paragraph boundaries. `[[multi\n\nline]]` doesn't render as a link.
* **Inside code blocks** — `[[…]]` inside a `code_block` node still matches because `node.isText` is true for the inner text node. This may decorate code text unintentionally; a future fix would skip nodes whose `parent.type.name === 'code_block'`.

## Related

* [[Wiki Links]] — the feature view
* [[Editor Component]] — the wrapper
* [[useGraph]] — uses the same regex to build the graph
* [[Milkdown Integration]]
