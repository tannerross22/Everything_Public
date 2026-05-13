import { $prose } from '@milkdown/utils'
import { Plugin, PluginKey } from '@milkdown/prose/state'
import { Decoration, DecorationSet } from '@milkdown/prose/view'
import type { Node } from '@milkdown/prose/model'

const wikiLinkPluginKey = new PluginKey('wikiLink')

/**
 * Creates a Milkdown plugin that:
 * 1. Scans the document for [[wiki link]] patterns
 * 2. Adds styled decorations over them
 * 3. Handles clicks to navigate to linked notes
 */
export function createWikiLinkPlugin(onLinkClick: (target: string) => void) {
  return $prose(() => {
    return new Plugin({
      key: wikiLinkPluginKey,

      state: {
        init(_, state) {
          return findWikiLinks(state.doc)
        },
        apply(tr, oldDecorations) {
          if (tr.docChanged) {
            return findWikiLinks(tr.doc)
          }
          return oldDecorations
        },
      },

      props: {
        decorations(state) {
          return this.getState(state)
        },

        handleClick(_view, _pos, event) {
          const target = event.target as HTMLElement
          const linkEl = target.closest('.wiki-link')
          if (linkEl) {
            const linkTarget = linkEl.getAttribute('data-target')
            if (linkTarget) {
              onLinkClick(linkTarget)
              return true
            }
          }
          return false
        },
      },
    })
  })
}

/**
 * Scan a ProseMirror document for [[...]] patterns and return decorations
 */
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
