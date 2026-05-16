import { useCallback, useRef, useEffect, useState } from 'react'
import { createHunspellFromStrings } from 'hunspell-wasm'

interface HunspellInstance {
  checker: any
  isReady: boolean
}

// Global hunspell instance shared across all uses
let hunspellInstance: HunspellInstance = {
  checker: null,
  isReady: false,
}

// Callback to notify when hunspell is ready
let onReadyCallback: ((checker: any) => void) | null = null

export function onHunspellReady(callback: (checker: any) => void) {
  onReadyCallback = callback
  if (hunspellInstance.isReady && hunspellInstance.checker) {
    console.log('[onHunspellReady] Hunspell already ready, calling callback immediately')
    callback(hunspellInstance.checker)
  }
}

async function initializeHunspell() {
  if (hunspellInstance.isReady) {
    console.log('[initializeHunspell] Already initialized')
    return hunspellInstance.checker
  }

  try {
    console.log('[initializeHunspell] Fetching dictionary files...')
    // Fetch dictionary files from public directory
    const [affResponse, dicResponse] = await Promise.all([
      fetch('/dicts/en_US.aff'),
      fetch('/dicts/en_US.dic'),
    ])

    if (!affResponse.ok || !dicResponse.ok) {
      throw new Error(`Failed to load dictionary files: aff=${affResponse.ok}, dic=${dicResponse.ok}`)
    }

    console.log('[initializeHunspell] Dictionary files fetched, creating hunspell instance...')
    const affText = await affResponse.text()
    const dicText = await dicResponse.text()

    // Initialize hunspell with the dictionaries
    const checker = await createHunspellFromStrings(affText, dicText)

    console.log('[initializeHunspell] Hunspell instance created:', checker)

    hunspellInstance.checker = checker
    hunspellInstance.isReady = true

    // Call ready callback if set
    if (onReadyCallback) {
      console.log('[initializeHunspell] Calling onReady callback')
      onReadyCallback(checker)
    }

    console.log('[Hunspell] Initialized successfully')
    return checker
  } catch (error) {
    console.error('Failed to initialize Hunspell:', error)
    hunspellInstance.isReady = false
    return null
  }
}

export function useHunspell() {
  const checkerRef = useRef<any>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    console.log('[useHunspell] Initializing hunspell...')
    initializeHunspell().then((checker) => {
      if (checker) {
        console.log('[useHunspell] Hunspell initialized successfully')
        checkerRef.current = checker
        setIsReady(true)
      } else {
        console.error('[useHunspell] Failed to initialize hunspell')
        setIsReady(false)
      }
    })
  }, [])

  const checkWord = useCallback(
    async (word: string): Promise<string[]> => {
      if (!checkerRef.current || !isReady) return []

      try {
        // Use getSpellingSuggestions() from hunspell-wasm
        const suggestions = checkerRef.current.getSpellingSuggestions(word)
        // Return up to 2 suggestions
        return (suggestions || []).slice(0, 2)
      } catch (error) {
        console.warn('Hunspell getSpellingSuggestions error:', error)
        return []
      }
    },
    [isReady]
  )

  const isCorrect = useCallback(
    (word: string): boolean => {
      if (!checkerRef.current || !isReady) return true
      try {
        // Use testSpelling() from hunspell-wasm
        return checkerRef.current.testSpelling(word)
      } catch (error) {
        console.warn('Hunspell testSpelling error:', error)
        return true
      }
    },
    [isReady]
  )

  return { checkWord, isCorrect, isReady }
}
