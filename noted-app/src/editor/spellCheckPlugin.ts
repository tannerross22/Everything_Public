import { $prose } from '@milkdown/utils'
import { Decoration, DecorationSet } from '@milkdown/prose/view'
import { Plugin, PluginKey } from '@milkdown/prose/state'

let hunspellChecker: any = null
let isHunspellReady = false

export function setHunspellChecker(checker: any) {
  hunspellChecker = checker
  isHunspellReady = !!checker
}

function isWordMisspelled(word: string): boolean {
  // Don't check if hunspell isn't ready yet
  if (!hunspellChecker || !isHunspellReady) {
    return false
  }

  if (!word || word.length === 0) return false

  try {
    // Use testSpelling() method from hunspell-wasm
    // Returns true if the word is spelled correctly
    const isCorrect = hunspellChecker.testSpelling(word)
    return !isCorrect
  } catch (error) {
    console.warn(`[SpellCheck] Error checking word "${word}":`, error)
    return false
  }
}

function findMisspelledWords(doc: any): DecorationSet {
  if (!hunspellChecker || !isHunspellReady) return DecorationSet.empty

  const decorations: Decoration[] = []

  doc.descendants((node: any, pos: number) => {
    if (!node.isText) return

    const text = node.text || ''
    const wordRegex = /[\w']+/g
    let match

    while ((match = wordRegex.exec(text)) !== null) {
      const word = match[0]
      if (isWordMisspelled(word)) {
        const from = pos + match.index
        const to = from + word.length

        decorations.push(
          Decoration.inline(from, to, {
            class: 'spell-error',
            title: `Misspelled: ${word}`,
          })
        )
      }
    }
  })

  return DecorationSet.create(doc, decorations)
}

export const spellCheckPlugin = $prose(() => {
  const pluginKey = new PluginKey('spellCheck')

  return new Plugin({
    key: pluginKey,
    state: {
      init(_, state) {
        return findMisspelledWords(state.doc)
      },
      apply(tr, _decorationSet, _oldState, newState) {
        if (tr.docChanged) {
          return findMisspelledWords(newState.doc)
        }
        return _decorationSet
      },
    },
    props: {
      decorations(state) {
        return pluginKey.getState(state)
      },
    },
  })
})
