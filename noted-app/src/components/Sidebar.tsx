import { useState } from 'react'
import type { FileTreeNode } from '../types'
import GitPanel from './GitPanel'
import { DULL_COLOR } from '../hooks/useFolderColors'

interface SidebarProps {
  fileTree: FileTreeNode[]
  activeNotePath: string | null
  activeNoteName: string | null
  onOpenNote: (path: string) => void | Promise<void>
  onCreateNote: (name: string, folderPath?: string) => void
  onCreateFolder: (fullPath: string) => void
  onDeleteFolder: (folderPath: string) => void
  onDeleteNote?: () => void
  onMoveItem: (oldPath: string, newFolderPath: string) => void
  onChangeVault: () => void
  onRenameNote?: (oldPath: string, newName: string) => Promise<any>
  vaultDir: string
  folderColors: Record<string, string>
}

type CreatingState = { type: 'note' | 'folder'; parentPath: string } | null
type CtxMenu = { x: number; y: number; node: FileTreeNode } | null

/** OS-agnostic path join for renderer (no Node path module available) */
function pathJoin(parent: string, name: string) {
  const sep = parent.includes('\\') ? '\\' : '/'
  return `${parent}${sep}${name}`
}

export default function Sidebar({
  fileTree,
  activeNotePath,
  activeNoteName,
  onOpenNote,
  onCreateNote,
  onCreateFolder,
  onDeleteFolder,
  onDeleteNote,
  onMoveItem,
  onChangeVault,
  onRenameNote,
  vaultDir,
  folderColors,
}: SidebarProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [draggingPath, setDraggingPath] = useState<string | null>(null)
  const [dragOverPath, setDragOverPath] = useState<string | null>(null)
  const [creating, setCreating] = useState<CreatingState>(null)
  const [createValue, setCreateValue] = useState('')
  const [renamingPath, setRenamingPath] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [ctxMenu, setCtxMenu] = useState<CtxMenu>(null)

  // ── Folder toggle ──────────────────────────────────────────────────────────
  const toggleFolder = (path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(path) ? next.delete(path) : next.add(path)
      return next
    })
  }

  // ── Create ────────────────────────────────────────────────────────────────
  const startCreating = (type: 'note' | 'folder', parentPath: string) => {
    setCtxMenu(null)
    if (parentPath !== vaultDir) {
      setExpanded((prev) => new Set([...prev, parentPath]))
    }
    setCreating({ type, parentPath })
    setCreateValue('')
  }

  const commitCreate = () => {
    if (!creating || !createValue.trim()) {
      setCreating(null)
      return
    }
    if (creating.type === 'note') {
      onCreateNote(createValue.trim(), creating.parentPath)
    } else {
      onCreateFolder(pathJoin(creating.parentPath, createValue.trim()))
    }
    setCreating(null)
    setCreateValue('')
  }

  const handleCreateKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') commitCreate()
    if (e.key === 'Escape') { setCreating(null); setCreateValue('') }
  }

  // ── Rename ────────────────────────────────────────────────────────────────
  const startRename = (node: FileTreeNode) => {
    setCtxMenu(null)
    setRenamingPath(node.path)
    setRenameValue(node.name)
  }

  const commitRename = async (oldPath: string) => {
    if (renameValue.trim() && onRenameNote) {
      try { await onRenameNote(oldPath, renameValue.trim()) } catch {}
    }
    setRenamingPath(null)
  }

  const handleRenameKeyDown = (e: React.KeyboardEvent, path: string) => {
    if (e.key === 'Enter') commitRename(path)
    if (e.key === 'Escape') setRenamingPath(null)
  }

  // ── Delete ────────────────────────────────────────────────────────────────
  const handleDeleteActive = async () => {
    if (!onDeleteNote || !activeNoteName) return
    if (await window.api.confirm(`Delete "${activeNoteName}"?`)) {
      onDeleteNote()
    }
  }

  const handleDeleteFolder = async (node: FileTreeNode) => {
    setCtxMenu(null)
    const confirmed = await window.api.confirm(
      `Delete folder "${node.name}" and everything inside it?`
    )
    if (confirmed) onDeleteFolder(node.path)
  }

  const handleDeleteNote = async (node: FileTreeNode) => {
    setCtxMenu(null)
    if (!onDeleteNote) return
    if (await window.api.confirm(`Delete "${node.name}"?`)) {
      await onOpenNote(node.path)
      onDeleteNote()
    }
  }

  // ── Context menu ──────────────────────────────────────────────────────────
  const openCtxMenu = (e: React.MouseEvent, node: FileTreeNode) => {
    e.preventDefault()
    e.stopPropagation()
    setCtxMenu({ x: e.clientX, y: e.clientY, node })
  }

  // ── Drag & Drop ───────────────────────────────────────────────────────────
  const handleDragStart = (e: React.DragEvent, path: string) => {
    e.stopPropagation()
    setDraggingPath(path)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', path)
  }

  const handleDragOver = (e: React.DragEvent, targetPath: string) => {
    e.preventDefault()
    e.stopPropagation()
    if (targetPath !== draggingPath) {
      e.dataTransfer.dropEffect = 'move'
      setDragOverPath(targetPath)
    }
  }

  const handleDrop = (e: React.DragEvent, targetPath: string) => {
    e.preventDefault()
    e.stopPropagation()
    const src = e.dataTransfer.getData('text/plain') || draggingPath
    if (
      src &&
      src !== targetPath &&
      !targetPath.startsWith(src + '\\') &&
      !targetPath.startsWith(src + '/')
    ) {
      onMoveItem(src, targetPath)
    }
    setDraggingPath(null)
    setDragOverPath(null)
  }

  const handleDragEnd = () => {
    setDraggingPath(null)
    setDragOverPath(null)
  }

  // ── Inline create input ───────────────────────────────────────────────────
  const renderCreateInput = (depth: number) => (
    <div
      className="sidebar-create-inline"
      style={{ paddingLeft: `${12 + depth * 16}px` }}
    >
      <input
        type="text"
        className="sidebar-input"
        value={createValue}
        onChange={(e) => setCreateValue(e.target.value)}
        onKeyDown={handleCreateKeyDown}
        onBlur={commitCreate}
        placeholder={creating?.type === 'folder' ? 'Folder name...' : 'Note name...'}
        autoFocus
      />
    </div>
  )

  // ── Recursive tree renderer ───────────────────────────────────────────────
  // inheritedColor: the top-level folder color passed down to all descendants
  const renderNode = (node: FileTreeNode, depth: number, inheritedColor?: string): React.ReactNode => {
    const indent = 12 + depth * 16
    const isRenaming = renamingPath === node.path

    // Resolve the icon color for this node:
    // depth-0 folders use their assigned palette color; everything else inherits or falls back to dull
    const iconColor: string =
      depth === 0 && node.type === 'folder'
        ? (folderColors[node.path] ?? DULL_COLOR)
        : (inheritedColor ?? DULL_COLOR)

    const iconStyle = { '--icon-color': iconColor } as React.CSSProperties

    if (node.type === 'folder') {
      const isOpen = expanded.has(node.path)
      const isDragTarget = dragOverPath === node.path

      return (
        <div key={node.path}>
          {isRenaming ? (
            <div className="sidebar-note-rename" style={{ paddingLeft: `${indent}px` }}>
              <input
                type="text"
                className="sidebar-input"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={(e) => handleRenameKeyDown(e, node.path)}
                onBlur={() => commitRename(node.path)}
                autoFocus
              />
            </div>
          ) : (
            <div
              className={`sidebar-folder-row${isDragTarget ? ' drag-over' : ''}${draggingPath === node.path ? ' dragging' : ''}`}
              style={{ paddingLeft: `${indent}px` }}
              onClick={() => toggleFolder(node.path)}
              onContextMenu={(e) => openCtxMenu(e, node)}
              draggable
              onDragStart={(e) => handleDragStart(e, node.path)}
              onDragOver={(e) => handleDragOver(e, node.path)}
              onDrop={(e) => handleDrop(e, node.path)}
              onDragEnd={handleDragEnd}
            >
              <span className="folder-chevron">{isOpen ? '▾' : '▸'}</span>
              <span className="tree-icon folder-icon" style={iconStyle} />
              <span className="tree-name">{node.name}</span>
            </div>
          )}
          {isOpen && (
            <div>
              {(node.children ?? []).map((child) => renderNode(child, depth + 1, iconColor))}
              {creating?.parentPath === node.path && renderCreateInput(depth + 1)}
            </div>
          )}
        </div>
      )
    }

    // File node
    return isRenaming ? (
      <div key={node.path} className="sidebar-note-rename" style={{ paddingLeft: `${indent}px` }}>
        <input
          type="text"
          className="sidebar-input"
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
          onKeyDown={(e) => handleRenameKeyDown(e, node.path)}
          onBlur={() => commitRename(node.path)}
          autoFocus
        />
      </div>
    ) : (
      <div
        key={node.path}
        className={`sidebar-note${node.path === activeNotePath ? ' active' : ''}${draggingPath === node.path ? ' dragging' : ''}`}
        style={{ paddingLeft: `${indent}px` }}
        onClick={() => onOpenNote(node.path)}
        onContextMenu={(e) => openCtxMenu(e, node)}
        draggable
        onDragStart={(e) => handleDragStart(e, node.path)}
        onDragEnd={handleDragEnd}
      >
        <span className="tree-icon file-icon" style={iconStyle} />
        <div className="note-info">
          <span className="note-name">{node.name}</span>
          {node.modifiedAt != null && (
            <span className="note-date">
              {new Date(node.modifiedAt).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    )
  }

  const vaultLabel = vaultDir.split(/[/\\]/).pop() || vaultDir

  return (
    <div className="sidebar" onClick={() => setCtxMenu(null)}>
      {/* ── Header ── */}
      <div className="sidebar-header">
        <h2 className="sidebar-title">Noted</h2>
        <div className="sidebar-actions">
          {onDeleteNote && activeNoteName && (
            <button
              className="sidebar-btn icon-btn delete-btn"
              onClick={(e) => { e.stopPropagation(); handleDeleteActive() }}
              title="Delete current note"
            >
              −
            </button>
          )}
          {/* New Note */}
          <button
            className="sidebar-btn icon-btn"
            onClick={(e) => { e.stopPropagation(); startCreating('note', vaultDir) }}
            title="New Note (Ctrl+N)"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="1" y="1" width="9" height="11" rx="1" stroke="currentColor" strokeWidth="1.2"/>
              <line x1="3" y1="4.5" x2="7" y2="4.5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round"/>
              <line x1="3" y1="6.5" x2="7" y2="6.5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round"/>
              <line x1="11" y1="8" x2="11" y2="13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
              <line x1="8.5" y1="10.5" x2="13.5" y2="10.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
          </button>
          {/* New Folder */}
          <button
            className="sidebar-btn icon-btn"
            onClick={(e) => { e.stopPropagation(); startCreating('folder', vaultDir) }}
            title="New Folder"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M1 3.5C1 3 1.45 2.5 2 2.5H5.5L7 4.5H12C12.55 4.5 13 4.95 13 5.5V10.5C13 11.05 12.55 11.5 12 11.5H2C1.45 11.5 1 11.05 1 10.5V3.5Z" stroke="currentColor" strokeWidth="1.2"/>
              <line x1="7" y1="6.5" x2="7" y2="9.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
              <line x1="5.5" y1="8" x2="8.5" y2="8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
      </div>

      {/* ── File Tree ── */}
      <div
        className={`sidebar-notes${dragOverPath === '__root__' ? ' drag-over-root' : ''}`}
        onDragOver={(e) => handleDragOver(e, '__root__')}
        onDrop={(e) => handleDrop(e, vaultDir)}
      >
        {creating?.parentPath === vaultDir && renderCreateInput(0)}
        {fileTree.map((node) => renderNode(node, 0))}
        {fileTree.length === 0 && !creating && (
          <div className="sidebar-empty">No notes yet. Click + to create one.</div>
        )}
      </div>

      <GitPanel vaultDir={vaultDir} />

      <div className="sidebar-footer">
        <button
          className="sidebar-btn vault-btn"
          onClick={onChangeVault}
          title="Change vault directory"
        >
          {vaultLabel}
        </button>
      </div>

      {/* ── Context Menu ── */}
      {ctxMenu && (
        <div
          className="context-menu"
          style={{ top: ctxMenu.y, left: ctxMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          {ctxMenu.node.type === 'folder' ? (
            <>
              <div
                className="context-menu-item"
                onClick={() => startCreating('note', ctxMenu.node.path)}
              >
                New Note Here
              </div>
              <div
                className="context-menu-item"
                onClick={() => startCreating('folder', ctxMenu.node.path)}
              >
                New Folder Here
              </div>
              <div
                className="context-menu-item"
                onClick={() => startRename(ctxMenu.node)}
              >
                Rename
              </div>
              <div
                className="context-menu-item danger"
                onClick={() => handleDeleteFolder(ctxMenu.node)}
              >
                Delete Folder
              </div>
            </>
          ) : (
            <>
              <div
                className="context-menu-item"
                onClick={() => { onOpenNote(ctxMenu.node.path); setCtxMenu(null) }}
              >
                Open
              </div>
              <div
                className="context-menu-item"
                onClick={() => startRename(ctxMenu.node)}
              >
                Rename
              </div>
              <div
                className="context-menu-item danger"
                onClick={() => handleDeleteNote(ctxMenu.node)}
              >
                Delete
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
