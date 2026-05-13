import { useEffect } from 'react'
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
    <div className="context-menu" style={{ top: `${y}px`, left: `${x}px` }}>
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
