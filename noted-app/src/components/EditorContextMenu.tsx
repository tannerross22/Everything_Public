import { useEffect } from 'react'

interface EditorContextMenuProps {
  x: number
  y: number
  selectedText: string
  suggestions: string[]
  onCopy: () => void
  onPaste: () => void
  onSelectSuggestion: (suggestion: string) => void
  onInsertLink: () => void
  onClose: () => void
}

export default function EditorContextMenu({
  x,
  y,
  selectedText,
  suggestions,
  onCopy,
  onPaste,
  onSelectSuggestion,
  onInsertLink,
  onClose,
}: EditorContextMenuProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    const handleClick = (e: MouseEvent) => {
      const menu = document.querySelector('.editor-context-menu')
      if (menu && !menu.contains(e.target as Node)) {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('click', handleClick)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('click', handleClick)
    }
  }, [onClose])

  const handleCopy = () => {
    onCopy()
    onClose()
  }

  const handlePaste = () => {
    onPaste()
    onClose()
  }

  const handleSelectSuggestion = (suggestion: string) => {
    onSelectSuggestion(suggestion)
    onClose()
  }

  const handleInsertLink = () => {
    onInsertLink()
    onClose()
  }

  return (
    <div className="editor-context-menu context-menu" style={{ top: `${y}px`, left: `${x}px` }}>
      {suggestions.length > 0 && (
        <>
          {suggestions.map((suggestion) => (
            <div
              key={suggestion}
              className="context-menu-item suggestion"
              onClick={() => handleSelectSuggestion(suggestion)}
            >
              {suggestion}
            </div>
          ))}
          <div className="context-menu-separator" />
        </>
      )}
      {selectedText && (
        <>
          <div className="context-menu-item" onClick={handleCopy}>
            Copy
          </div>
          <div className="context-menu-item" onClick={handleInsertLink}>
            Insert Link
          </div>
          <div className="context-menu-separator" />
        </>
      )}
      <div className="context-menu-item" onClick={handlePaste}>
        Paste
      </div>
    </div>
  )
}
