import { useEffect, useRef } from 'react'

interface SpellChecker {
  check: (word: string) => boolean
  getSuggestions: (word: string, limit?: number) => string[]
}

export function useSpellChecker(): SpellChecker | null {
  const checkerRef = useRef<SpellChecker | null>(null)

  useEffect(() => {
    const initSpellChecker = async () => {
      try {
        console.log('[SpellChecker] Starting initialization...')

        // Dynamic import to avoid bundling the large dictionary files upfront
        const TypoModule = await import('typo-js')
        console.log('[SpellChecker] Typo module imported')

        const Typo = (TypoModule as any).default || (TypoModule as any)
        console.log('[SpellChecker] Typo constructor type:', typeof Typo)

        // Load dictionary files manually
        console.log('[SpellChecker] Loading dictionary files...')
        const affPath = new URL('../../node_modules/typo-js/dictionaries/en_US/en_US.aff', import.meta.url).href
        const dicPath = new URL('../../node_modules/typo-js/dictionaries/en_US/en_US.dic', import.meta.url).href

        console.log('[SpellChecker] Dictionary paths:', { affPath, dicPath })

        const [affData, dicData] = await Promise.all([
          fetch(affPath).then(r => r.text()),
          fetch(dicPath).then(r => r.text()),
        ])

        console.log('[SpellChecker] Dictionary files loaded, initializing Typo...')

        // Initialize with loaded dictionary data
        const checker = new Typo('en_US', affData, dicData) as any
        console.log('[SpellChecker] Checker initialized successfully')

        checkerRef.current = {
          check: (word: string) => {
            if (!word || word.length === 0) return true
            try {
              // Normalize word - remove special chars except apostrophes
              const normalizedWord = word.toLowerCase().replace(/[^a-z']/g, '')
              if (normalizedWord.length === 0) return true
              const result = checker.check(normalizedWord)
              console.log(`[SpellChecker] Checking word "${word}" (normalized: "${normalizedWord}"):`, result)
              return result
            } catch (e) {
              console.warn('[SpellChecker] Spell check error for word:', word, e)
              return true // If check fails, assume word is correct
            }
          },
          getSuggestions: (word: string, limit = 2) => {
            if (!word || word.length === 0) return []
            try {
              const normalizedWord = word.toLowerCase().replace(/[^a-z']/g, '')
              if (normalizedWord.length === 0) return []
              const suggestions = checker.suggest(normalizedWord) || []
              console.log(`[SpellChecker] Suggestions for "${word}" (normalized: "${normalizedWord}"):`, suggestions.slice(0, limit))
              return suggestions.slice(0, limit)
            } catch (e) {
              console.warn('[SpellChecker] Spell suggest error for word:', word, e)
              return []
            }
          },
        }
        console.log('[SpellChecker] Initialization complete')
      } catch (error) {
        console.error('[SpellChecker] Failed to initialize spell checker:', error)
        checkerRef.current = null
      }
    }

    initSpellChecker()
  }, [])

  return checkerRef.current
}
