import { useState, useEffect, useRef, useCallback } from 'react'

interface FindBarProps {
  visible: boolean
  onClose: () => void
  /** The DOM element to search within (the .editor-container) */
  containerEl: HTMLElement | null
}

/** Walk all text nodes inside an element */
function getTextNodes(el: HTMLElement): Text[] {
  const nodes: Text[] = []
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
  let node: Text | null
  while ((node = walker.nextNode() as Text | null)) {
    nodes.push(node)
  }
  return nodes
}

export default function FindBar({ visible, onClose, containerEl }: FindBarProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [query, setQuery] = useState('')
  const [matches, setMatches] = useState<Range[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)

  // Focus the input when the bar becomes visible
  useEffect(() => {
    if (visible) {
      setTimeout(() => inputRef.current?.focus(), 50)
    } else {
      // Clear highlights when closing
      setQuery('')
      setMatches([])
      setCurrentIndex(0)
      try { CSS.highlights.delete('find-matches'); CSS.highlights.delete('find-current') } catch {}
    }
  }, [visible])

  // Search and build highlights whenever query or container changes
  const runSearch = useCallback((searchTerm: string) => {
    // Clear previous highlights
    try { CSS.highlights.delete('find-matches'); CSS.highlights.delete('find-current') } catch {}

    if (!searchTerm || !containerEl) {
      setMatches([])
      setCurrentIndex(0)
      return
    }

    const proseMirror = containerEl.querySelector('.ProseMirror') as HTMLElement
    if (!proseMirror) {
      setMatches([])
      setCurrentIndex(0)
      return
    }

    const textNodes = getTextNodes(proseMirror)
    const term = searchTerm.toLowerCase()
    const foundRanges: Range[] = []

    for (const textNode of textNodes) {
      const text = (textNode.textContent || '').toLowerCase()
      let startPos = 0
      while (startPos < text.length) {
        const idx = text.indexOf(term, startPos)
        if (idx === -1) break
        const range = document.createRange()
        range.setStart(textNode, idx)
        range.setEnd(textNode, idx + searchTerm.length)
        foundRanges.push(range)
        startPos = idx + 1
      }
    }

    setMatches(foundRanges)
    const newIndex = foundRanges.length > 0 ? 0 : -1
    setCurrentIndex(newIndex)

    // Apply CSS highlights
    if (foundRanges.length > 0) {
      const allHighlight = new Highlight(...foundRanges)
      CSS.highlights.set('find-matches', allHighlight)

      // Highlight and scroll to the current match
      if (newIndex >= 0) {
        const currentHighlight = new Highlight(foundRanges[newIndex])
        CSS.highlights.set('find-current', currentHighlight)
        foundRanges[newIndex].startContainer.parentElement?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        })
      }
    }
  }, [containerEl])

  // Re-run search when query changes
  useEffect(() => {
    runSearch(query)
  }, [query, runSearch])

  // Update current highlight when navigating
  const goToMatch = useCallback((index: number) => {
    if (matches.length === 0) return
    // Wrap around
    const wrapped = ((index % matches.length) + matches.length) % matches.length
    setCurrentIndex(wrapped)

    try {
      CSS.highlights.delete('find-current')
      const currentHighlight = new Highlight(matches[wrapped])
      CSS.highlights.set('find-current', currentHighlight)
      matches[wrapped].startContainer.parentElement?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    } catch {}
  }, [matches])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (e.shiftKey) {
        goToMatch(currentIndex - 1)
      } else {
        goToMatch(currentIndex + 1)
      }
    }
    if (e.key === 'Escape') {
      onClose()
    }
  }

  if (!visible) return null

  return (
    <div className="find-bar">
      <input
        ref={inputRef}
        type="text"
        className="find-input"
        placeholder="Find..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <span className="find-count">
        {query ? (matches.length > 0 ? `${currentIndex + 1}/${matches.length}` : '0 results') : ''}
      </span>
      <button
        className="find-nav-btn"
        onClick={() => goToMatch(currentIndex - 1)}
        disabled={matches.length === 0}
        title="Previous (Shift+Enter)"
      >
        &#x25B2;
      </button>
      <button
        className="find-nav-btn"
        onClick={() => goToMatch(currentIndex + 1)}
        disabled={matches.length === 0}
        title="Next (Enter)"
      >
        &#x25BC;
      </button>
      <button
        className="find-close-btn"
        onClick={onClose}
        title="Close (Esc)"
      >
        ×
      </button>
    </div>
  )
}
