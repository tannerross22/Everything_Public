import { $prose } from '@milkdown/utils'
import { Decoration, DecorationSet } from '@milkdown/prose/view'
import { Plugin, PluginKey } from '@milkdown/prose/state'

interface SpellCheckCache {
  [word: string]: boolean
}

let spellCheckCache: SpellCheckCache = {}
let pendingChecks = new Set<string>()

async function checkWordWithLanguageTool(word: string): Promise<boolean> {
  const cacheKey = word.toLowerCase()
  if (cacheKey in spellCheckCache) {
    return spellCheckCache[cacheKey]
  }

  try {
    const response = await fetch('https://api.languagetool.org/v2/check', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        text: word,
        language: 'en-US',
        disabledRules: 'CONTRACTIONS',
      }).toString(),
    })

    if (!response.ok) {
      spellCheckCache[cacheKey] = true
      return true
    }

    const data = await response.json()
    const isCorrect = !data.matches || data.matches.length === 0
    spellCheckCache[cacheKey] = isCorrect
    return isCorrect
  } catch {
    spellCheckCache[cacheKey] = true
    return true
  }
}

function findMisspelledWords(doc: any): DecorationSet {
  const decorations: Decoration[] = []

  doc.descendants((node: any, pos: number) => {
    if (!node.isText) return

    const text = node.text || ''
    const wordRegex = /[\w']+/g
    let match

    while ((match = wordRegex.exec(text)) !== null) {
      const word = match[0]
      const cacheKey = word.toLowerCase()

      // Check cache first
      if (cacheKey in spellCheckCache) {
        if (!spellCheckCache[cacheKey]) {
          const from = pos + match.index
          const to = from + word.length
          decorations.push(
            Decoration.inline(from, to, {
              class: 'spell-error',
              title: `Misspelled: ${word}`,
            })
          )
        }
      } else if (!pendingChecks.has(cacheKey)) {
        // Queue this word for checking
        pendingChecks.add(cacheKey)
        checkWordWithLanguageTool(word)
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
