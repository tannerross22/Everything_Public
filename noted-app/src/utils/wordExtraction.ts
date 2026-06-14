// Extract the word at a given position in text
export function extractWordAtPosition(element: Node, offset: number): { word: string; startOffset: number; endOffset: number } | null {
  let text = ''
  let currentOffset = 0

  // Walk through text nodes to find the right one
  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    null,
  )

  let textNode: Node | null = null
  while ((textNode = walker.nextNode())) {
    const nodeText = textNode.textContent || ''
    if (currentOffset + nodeText.length >= offset) {
      // Found the text node containing our position
      const posInNode = offset - currentOffset
      text = nodeText
      const wordMatch = extractWordFromText(text, posInNode)
      if (wordMatch) {
        return {
          word: wordMatch.word,
          startOffset: currentOffset + wordMatch.start,
          endOffset: currentOffset + wordMatch.end,
        }
      }
      return null
    }
    currentOffset += nodeText.length
  }

  return null
}

// Extract word from text at a specific position
function extractWordFromText(text: string, position: number): { word: string; start: number; end: number } | null {
  // Find word boundaries (alphanumeric + apostrophe for contractions)
  const wordPattern = /\b[\w']+\b/g
  let match

  while ((match = wordPattern.exec(text)) !== null) {
    if (match.index <= position && position <= match.index + match[0].length) {
      return {
        word: match[0],
        start: match.index,
        end: match.index + match[0].length,
      }
    }
  }

  return null
}

// Get the word under cursor in the ProseMirror editor
export function getWordAtMousePosition(event: MouseEvent): { word: string; startOffset: number; endOffset: number } | null {
  console.log('[WordExtraction] Getting word at position:', { x: event.clientX, y: event.clientY })

  const target = event.target as Node
  if (!target) {
    console.log('[WordExtraction] No target element')
    return null
  }

  // Find the text node at the click position
  const range = document.caretRangeFromPoint(event.clientX, event.clientY)
  console.log('[WordExtraction] Caret range:', range)
  if (!range) {
    console.log('[WordExtraction] No caret range found')
    return null
  }

  console.log('[WordExtraction] Range start container:', range.startContainer, 'offset:', range.startOffset)
  const result = extractWordAtPosition(range.startContainer, range.startOffset)
  console.log('[WordExtraction] Extracted word:', result)
  return result
}
