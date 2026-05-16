import { useCallback } from 'react'

interface LanguageToolMatch {
  offset: number
  length: number
  message: string
  replacements: Array<{ value: string }>
  rule: { id: string }
}

interface LanguageToolResponse {
  matches: LanguageToolMatch[]
}

export function useLanguageTool() {
  const checkWord = useCallback(async (word: string): Promise<string[]> => {
    if (!word || word.length === 0) return []

    try {
      const response = await fetch('https://api.languagetool.org/v2/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          text: word,
          language: 'en-US',
        }).toString(),
      })

      if (!response.ok) {
        console.warn('LanguageTool API error:', response.status)
        return []
      }

      const data: LanguageToolResponse = await response.json()

      // Get the first match (usually the most relevant)
      if (data.matches && data.matches.length > 0) {
        const match = data.matches[0]
        // Return up to 2 suggestions
        return match.replacements
          .slice(0, 2)
          .map((r) => r.value)
      }

      return []
    } catch (error) {
      console.warn('LanguageTool check error:', error)
      return []
    }
  }, [])

  return { checkWord }
}
