import { useState } from 'react'
import type { NoteFile } from '../types'
import GitPanel from './GitPanel'

interface SidebarProps {
  notes: NoteFile[]
  activeNotePath: string | null
  activeNoteName: string | null
  onOpenNote: (path: string) => void
  onCreateNote: (name: string) => void
  onDeleteNote?: () => void
  onChangeVault: () => void
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
  vaultDir,
}: SidebarProps) {
  const [isCreating, setIsCreating] = useState(false)
  const [newNoteName, setNewNoteName] = useState('')

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
          <div
            key={note.path}
            className={`sidebar-note ${note.path === activeNotePath ? 'active' : ''}`}
            onClick={() => onOpenNote(note.path)}
          >
            <span className="note-name">{note.name}</span>
            <span className="note-date">
              {new Date(note.modifiedAt).toLocaleDateString()}
            </span>
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
    </div>
  )
}
