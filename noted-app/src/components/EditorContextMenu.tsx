import { useEffect, useRef, useState } from 'react'

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
  const menuRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ top: y, left: x })

  useEffect(() => {
    // Delay measurement until after render
    const timer = requestAnimationFrame(() => {
      if (menuRef.current) {
        const menuRect = menuRef.current.getBoundingClientRect()
        const viewportHeight = window.innerHeight
        const viewportWidth = window.innerWidth

        let adjustedTop = y
        let adjustedLeft = x

        console.log('[EditorContextMenu] Menu dimensions:', { width: menuRect.width, height: menuRect.height })
        console.log('[EditorContextMenu] Viewport:', { width: viewportWidth, height: viewportHeight })
        console.log('[EditorContextMenu] Click position:', { x, y })

        // If menu would go below viewport, position above the click point
        if (y + menuRect.height > viewportHeight) {
          adjustedTop = Math.max(0, y - menuRect.height - 8)
          console.log('[EditorContextMenu] Menu would go off-screen below, adjusting to:', adjustedTop)
        }

        // If menu would go right of viewport, position to the left
        if (x + menuRect.width > viewportWidth) {
          adjustedLeft = Math.max(0, viewportWidth - menuRect.width - 8)
          console.log('[EditorContextMenu] Menu would go off-screen right, adjusting to:', adjustedLeft)
        }

        setPosition({ top: adjustedTop, left: adjustedLeft })
      }
    })

    return () => cancelAnimationFrame(timer)
  }, [y, x])

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
    <div
      ref={menuRef}
      className="editor-context-menu context-menu"
      style={{ top: `${position.top}px`, left: `${position.left}px` }}
    >
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
