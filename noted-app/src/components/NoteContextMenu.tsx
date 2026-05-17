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
    // Estimate menu dimensions (2 items: Rename + Delete)
    const estimatedMenuHeight = 90
    const estimatedMenuWidth = 150

    let adjustedTop = y
    let adjustedLeft = x

    const viewportHeight = window.innerHeight
    const viewportWidth = window.innerWidth

    // If menu would go below viewport, position above the click point
    if (y + estimatedMenuHeight > viewportHeight - 10) {
      adjustedTop = Math.max(10, y - estimatedMenuHeight - 8)
    }

    // If menu would go right of viewport, position to the left
    if (x + estimatedMenuWidth > viewportWidth - 10) {
      adjustedLeft = Math.max(10, x - estimatedMenuWidth - 8)
    }

    console.log('[NoteContextMenu] Original position:', { y, x })
    console.log('[NoteContextMenu] Adjusted position:', { top: adjustedTop, left: adjustedLeft })
    console.log('[NoteContextMenu] Viewport:', { viewportHeight, viewportWidth })

    setPosition({ top: adjustedTop, left: adjustedLeft })
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
