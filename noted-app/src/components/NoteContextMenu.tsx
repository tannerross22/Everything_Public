import { useEffect, useRef, useState } from 'react'
import type { NoteFile } from '../types'

interface NoteContextMenuProps {
  x: number
  y: number
  note: NoteFile
  onDelete: () => void
  onRename: () => void
  onClose: () => void
}

export default function NoteContextMenu({
  x,
  y,
  note,
  onDelete,
  onRename,
  onClose,
}: NoteContextMenuProps) {
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

        console.log('[NoteContextMenu] Menu dimensions:', { width: menuRect.width, height: menuRect.height })
        console.log('[NoteContextMenu] Viewport:', { width: viewportWidth, height: viewportHeight })
        console.log('[NoteContextMenu] Click position:', { x, y })

        // If menu would go below viewport, position above the click point
        if (y + menuRect.height > viewportHeight) {
          adjustedTop = Math.max(0, y - menuRect.height - 8)
          console.log('[NoteContextMenu] Menu would go off-screen below, adjusting to:', adjustedTop)
        }

        // If menu would go right of viewport, position to the left
        if (x + menuRect.width > viewportWidth) {
          adjustedLeft = Math.max(0, viewportWidth - menuRect.width - 8)
          console.log('[NoteContextMenu] Menu would go off-screen right, adjusting to:', adjustedLeft)
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
      // Close if clicking outside the menu
      const menu = document.querySelector('.context-menu')
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

  const handleDelete = () => {
    onDelete()
    onClose()
  }

  const handleRename = () => {
    onRename()
    onClose()
  }

  return (
    <div
      ref={menuRef}
      className="context-menu"
      style={{ top: `${position.top}px`, left: `${position.left}px` }}
    >
      <div
        className="context-menu-item"
        onClick={handleRename}
      >
        Rename
      </div>
      <div
        className="context-menu-item danger"
        onClick={handleDelete}
      >
        Delete
      </div>
    </div>
  )
}
