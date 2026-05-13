import { useState } from 'react'
import type { NoteFile } from '../types'
import GitPanel from './GitPanel'
import NoteContextMenu from './NoteContextMenu'

interface SidebarProps {
  notes: NoteFile[]
  activeNotePath: string | null
  activeNoteName: string | null
  onOpenNote: (path: string) => void
  onCreateNote: (name: string) => void
  onDeleteNote?: () => void
  onChangeVault: () => void
  onRenameNote?: (oldPath: string, newName: string) => Promise<any>
  vaultDir: string
}

export default function Sidebar({
  notes,
  activeNotePath,
  activeNoteName,
  onOpenNote,
  onCreateNote,
  onDeleteNote,
  onChangeVault,
  onRenameNote,
  vaultDir,
}: SidebarProps) {
  const [isCreating, setIsCreating] = useState(false)
  const [newNoteName, setNewNoteName] = useState('')
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; note: NoteFile } | null>(null)
  const [renamingPath, setRenamingPath] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')

  const handleCreate = () => {
    if (newNoteName.trim()) {
      onCreateNote(newNoteName.trim())
      setNewNoteName('')
      setIsCreating(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleCreate()
    if (e.key === 'Escape') {
      setIsCreating(false)
      setNewNoteName('')
    }
  }

  const handleDelete = () => {
    if (onDeleteNote && activeNoteName) {
      if (confirm(`Delete "${activeNoteName}"?`)) {
        onDeleteNote()
      }
    }
  }

  const handleContextMenuDelete = () => {
    if (contextMenu && onDeleteNote) {
      if (confirm(`Delete "${contextMenu.note.name}"?`)) {
        onOpenNote(contextMenu.note.path)
        onDeleteNote()
      }
    }
  }

  const handleContextMenuRename = () => {
    if (contextMenu) {
      setRenamingPath(contextMenu.note.path)
      setRenameValue(contextMenu.note.name)
    }
  }

  const handleRenameConfirm = async (oldPath: string, newName: string) => {
    if (!newName.trim()) {
      setRenamingPath(null)
      return
    }
    try {
      if (onRenameNote) {
        const result = await onRenameNote(oldPath, newName)
        // Show success message (could add toast notification here)
        console.log(`Renamed to "${newName}" and updated ${result.updatedCount} references`)
      }
    } catch (error) {
      console.error('Failed to rename note:', error)
    } finally {
      setRenamingPath(null)
    }
  }

  const handleRenameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (renamingPath) {
        handleRenameConfirm(renamingPath, renameValue)
      }
    } else if (e.key === 'Escape') {
      setRenamingPath(null)
    }
  }

  const handleContextMenu = (e: React.MouseEvent, note: NoteFile) => {
    e.preventDefault()
    e.stopPropagation()
    setContextMenu({ x: e.clientX, y: e.clientY, note })
  }

  // Show just the last folder name for the vault path
  const vaultLabel = vaultDir.split(/[/\\]/).pop() || vaultDir

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2 className="sidebar-title">Noted</h2>
        <div className="sidebar-actions">
          {onDeleteNote && (
            <button
              className="sidebar-btn icon-btn delete-btn"
              onClick={handleDelete}
              title="Delete note"
            >
              -
            </button>
          )}
          <button
            className="sidebar-btn icon-btn"
            onClick={() => setIsCreating(true)}
            title="New Note (Ctrl+N)"
          >
            +
          </button>
        </div>
      </div>

      {isCreating && (
        <div className="sidebar-create">
          <input
            type="text"
            value={newNoteName}
            onChange={(e) => setNewNoteName(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={() => {
              if (!newNoteName.trim()) setIsCreating(false)
            }}
            placeholder="Note name..."
            autoFocus
            className="sidebar-input"
          />
        </div>
      )}

      <div className="sidebar-notes">
        {notes.map((note) => (
          <div key={note.path}>
            {renamingPath === note.path ? (
              <div className="sidebar-note-rename">
                <input
                  type="text"
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  onKeyDown={handleRenameKeyDown}
                  onBlur={() => handleRenameConfirm(note.path, renameValue)}
                  placeholder="Note name..."
                  autoFocus
                  className="sidebar-input"
                />
              </div>
            ) : (
              <div
                className={`sidebar-note ${note.path === activeNotePath ? 'active' : ''}`}
                onClick={() => onOpenNote(note.path)}
                onContextMenu={(e) => handleContextMenu(e, note)}
              >
                <span className="note-name">{note.name}</span>
                <span className="note-date">
                  {new Date(note.modifiedAt).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        ))}
        {notes.length === 0 && (
          <div className="sidebar-empty">
            No notes yet. Click + to create one.
          </div>
        )}
      </div>

      <GitPanel vaultDir={vaultDir} />

      <div className="sidebar-footer">
        <button className="sidebar-btn vault-btn" onClick={onChangeVault} title="Change vault directory">
          {vaultLabel}
        </button>
      </div>

      {contextMenu && (
        <NoteContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          note={contextMenu.note}
          onDelete={handleContextMenuDelete}
          onRename={handleContextMenuRename}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  )
}
