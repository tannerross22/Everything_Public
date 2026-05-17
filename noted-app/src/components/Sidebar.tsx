import { useState, useRef, useEffect } from 'react'
import type { FileTreeNode } from '../types'
import type { ModalConfig } from '../hooks/useModal'
import { DULL_COLOR } from '../hooks/useFolderColors'

type SortOrder = 'name-az' | 'name-za' | 'modified-new' | 'modified-old' | 'created-new' | 'created-old'

interface SidebarProps {
  fileTree: FileTreeNode[]
  activeNotePath: string | null
  activeNoteName: string | null
  onOpenNote: (path: string) => void | Promise<void>
  onOpenNoteInNewTab: (path: string) => Promise<void>
  onCreateNote: (name: string, folderPath?: string) => void
  onCreateFolder: (fullPath: string) => void
  onDeleteFolder: (folderPath: string) => void
  onDeleteNote?: () => void
  onMoveItem: (oldPath: string, newFolderPath: string) => void
  onChangeVault: () => void
  onRenameNote?: (oldPath: string, newName: string) => Promise<any>
  vaultDir: string
  folderColors: Record<string, string>
  clipboardPath: string | null
  onCopy: (path: string) => void
  onPaste: (destFolder: string) => void
  onConfirm?: (config: ModalConfig) => Promise<boolean>
  // Git sync props (managed by useGitSync in App.tsx)
  isRepo: boolean
  hasChanges: boolean
  syncing: boolean
  isProcessing: boolean
  showSynced: boolean
  onSync: () => void
  // Multi-select
  selectedPaths: Set<string>
  onSelectionChange: (paths: Set<string>) => void
  onDeleteItems: (items: Array<{ path: string; type: 'file' | 'folder' }>) => Promise<void>
  style?: React.CSSProperties
  className?: string
}

type CreatingState = { type: 'note' | 'folder'; parentPath: string } | null
type CtxMenu = { x: number; y: number; node: FileTreeNode | null } | null

/** OS-agnostic path join for renderer (no Node path module available) */
function pathJoin(parent: string, name: string) {
  const sep = parent.includes('\\') ? '\\' : '/'
  return `${parent}${sep}${name}`
}

// ── Multi-select helpers (defined outside component to avoid re-creation) ──
function flattenVisible(nodes: FileTreeNode[], expandedSet: Set<string>): FileTreeNode[] {
  const result: FileTreeNode[] = []
  for (const node of nodes) {
    result.push(node)
    if (node.type === 'folder' && expandedSet.has(node.path) && node.children) {
      result.push(...flattenVisible(node.children, expandedSet))
    }
  }
  return result
}

function findNodeInTree(nodes: FileTreeNode[], path: string): FileTreeNode | null {
  for (const node of nodes) {
    if (node.path === path) return node
    if (node.children) {
      const found = findNodeInTree(node.children, path)
      if (found) return found
    }
  }
  return null
}

export default function Sidebar({
  fileTree,
  activeNotePath,
  activeNoteName,
  onOpenNote,
  onOpenNoteInNewTab,
  onCreateNote,
  onCreateFolder,
  onDeleteFolder,
  onDeleteNote,
  onMoveItem,
  onChangeVault,
  onRenameNote,
  vaultDir,
  folderColors,
  clipboardPath,
  onCopy,
  onPaste,
  onConfirm,
  isRepo,
  hasChanges,
  syncing,
  isProcessing,
  showSynced,
  onSync,
  selectedPaths,
  onSelectionChange,
  onDeleteItems,
  style,
  className,
}: SidebarProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [draggingPath, setDraggingPath] = useState<string | null>(null)
  const [dragOverPath, setDragOverPath] = useState<string | null>(null)
  const [creating, setCreating] = useState<CreatingState>(null)
  const [createValue, setCreateValue] = useState('')
  const [renamingPath, setRenamingPath] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [ctxMenu, setCtxMenu] = useState<CtxMenu>(null)
  const [lastSelectedPath, setLastSelectedPath] = useState<string | null>(null)
  const ctxMenuRef = useRef<HTMLDivElement>(null)
  const [contextMenuPos, setContextMenuPos] = useState({ top: 0, left: 0 })

  // ── Folder toggle ──────────────────────────────────────────────────────────
  const toggleFolder = (path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(path) ? next.delete(path) : next.add(path)
      return next
    })
  }

  // ── Multi-select ───────────────────────────────────────────────────────────
  const handleNodeClick = (e: React.MouseEvent, node: FileTreeNode, defaultAction: () => void) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault()
      const next = new Set(selectedPaths)
      next.has(node.path) ? next.delete(node.path) : next.add(node.path)
      onSelectionChange(next)
      setLastSelectedPath(node.path)
    } else if (e.shiftKey && lastSelectedPath) {
      e.preventDefault()
      const flat = flattenVisible(fileTree, expanded)
      const lastIdx = flat.findIndex((n) => n.path === lastSelectedPath)
      const thisIdx = flat.findIndex((n) => n.path === node.path)
      if (lastIdx >= 0 && thisIdx >= 0) {
        const [from, to] = lastIdx <= thisIdx ? [lastIdx, thisIdx] : [thisIdx, lastIdx]
        onSelectionChange(new Set(flat.slice(from, to + 1).map((n) => n.path)))
      }
    } else {
      // Normal click: clear multi-select, select this item, run default action
      onSelectionChange(new Set([node.path]))
      setLastSelectedPath(node.path)
      defaultAction()
    }
  }

  const handleDeleteSelected = () => {
    if (selectedPaths.size === 0) return
    const items = Array.from(selectedPaths).map((path) => {
      const node = findNodeInTree(fileTree, path)
      return { path, type: (node?.type ?? 'file') as 'file' | 'folder' }
    })
    onDeleteItems(items)
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
    const confirmed = onConfirm
      ? await onConfirm({
          title: 'Delete Note',
          message: `Delete "${activeNoteName}"? This cannot be undone.`,
          confirmText: 'Delete',
          cancelText: 'Cancel',
          isDangerous: true,
        })
      : await window.api.confirm(`Delete "${activeNoteName}"?`)
    if (confirmed) {
      onDeleteNote()
    }
  }

  const handleDeleteFolder = async (node: FileTreeNode) => {
    setCtxMenu(null)
    const confirmed = onConfirm
      ? await onConfirm({
          title: 'Delete Folder',
          message: `Delete folder "${node.name}" and everything inside it? This cannot be undone.`,
          confirmText: 'Delete',
          cancelText: 'Cancel',
          isDangerous: true,
        })
      : await window.api.confirm(
          `Delete folder "${node.name}" and everything inside it?`
        )
    if (confirmed) onDeleteFolder(node.path)
  }

  const handleDeleteNote = async (node: FileTreeNode) => {
    setCtxMenu(null)
    if (!onDeleteNote) return
    const confirmed = onConfirm
      ? await onConfirm({
          title: 'Delete Note',
          message: `Delete "${node.name}"? This cannot be undone.`,
          confirmText: 'Delete',
          cancelText: 'Cancel',
          isDangerous: true,
        })
      : await window.api.confirm(`Delete "${node.name}"?`)
    if (confirmed) {
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

  // Smart positioning for context menu to avoid going off-screen
  useEffect(() => {
    if (!ctxMenu || !ctxMenuRef.current) return

    const timer = requestAnimationFrame(() => {
      if (ctxMenuRef.current) {
        const menuRect = ctxMenuRef.current.getBoundingClientRect()
        const viewportHeight = window.innerHeight
        const viewportWidth = window.innerWidth

        let adjustedTop = ctxMenu.y
        let adjustedLeft = ctxMenu.x

        // If menu would go below viewport, position above the click point
        if (ctxMenu.y + menuRect.height > viewportHeight) {
          adjustedTop = Math.max(0, ctxMenu.y - menuRect.height - 8)
        }

        // If menu would go right of viewport, position to the left
        if (ctxMenu.x + menuRect.width > viewportWidth) {
          adjustedLeft = Math.max(0, viewportWidth - menuRect.width - 8)
        }

        setContextMenuPos({ top: adjustedTop, left: adjustedLeft })
      }
    })

    return () => cancelAnimationFrame(timer)
  }, [ctxMenu])

  // Close context menu when clicking outside the sidebar
  useEffect(() => {
    if (!ctxMenu) return

    const handleClickOutside = (e: MouseEvent) => {
      // Check if the click target is inside the sidebar
      const sidebar = document.querySelector('.sidebar')
      if (sidebar && !sidebar.contains(e.target as Node)) {
        setCtxMenu(null)
      }
    }

    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [ctxMenu])

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

  // ── Keyboard shortcuts (Ctrl+C / Ctrl+V) ──────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+C to copy
      if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        // Don't copy if we're in an input field
        if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
          return
        }
        e.preventDefault()

        // Copy first selected item, or active note if nothing selected
        let pathToCopy: string | null = null
        if (selectedPaths.size > 0) {
          pathToCopy = Array.from(selectedPaths)[0]
        } else if (activeNotePath) {
          pathToCopy = activeNotePath
        }

        if (pathToCopy) {
          onCopy(pathToCopy)
        }
      }

      // Ctrl+V to paste
      if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
        // Don't paste if we're in an input field
        if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
          return
        }
        e.preventDefault()

        if (!clipboardPath) return

        // Paste to first selected folder, or vault root
        let pasteTarget = vaultDir
        if (selectedPaths.size > 0) {
          const firstSelected = Array.from(selectedPaths)[0]
          const node = findNodeInTree(fileTree, firstSelected)
          if (node?.type === 'folder') {
            pasteTarget = firstSelected
          }
        }

        onPaste(pasteTarget)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedPaths, activeNotePath, clipboardPath, fileTree, vaultDir, onCopy, onPaste])

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
              className={`sidebar-folder-row${isDragTarget ? ' drag-over' : ''}${draggingPath === node.path ? ' dragging' : ''}${selectedPaths.has(node.path) ? ' selected' : ''}`}
              style={{ paddingLeft: `${indent}px` }}
              onClick={(e) => handleNodeClick(e, node, () => toggleFolder(node.path))}
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
        className={`sidebar-note${node.path === activeNotePath ? ' active' : ''}${selectedPaths.has(node.path) ? ' selected' : ''}${draggingPath === node.path ? ' dragging' : ''}`}
        style={{ paddingLeft: `${indent}px` }}
        onClick={(e) => handleNodeClick(e, node, () => onOpenNote(node.path))}
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
    <div
      className={`sidebar${className ? ` ${className}` : ''}`}
      onClick={(e) => {
        setCtxMenu(null)
        // Clear selection when clicking sidebar background (not a tree node)
        if (e.target === e.currentTarget) onSelectionChange(new Set())
      }}
      style={style}
    >
      {/* ── Header ── */}
      <div className="sidebar-header">
        <h2 className="sidebar-title">Noted</h2>
        <div className="sidebar-actions">
          {/* Multi-select delete — shown when 2+ items selected */}
          {selectedPaths.size > 1 && (
            <button
              className="sidebar-btn icon-btn delete-btn multi-delete-btn"
              onClick={(e) => { e.stopPropagation(); handleDeleteSelected() }}
              title={`Delete ${selectedPaths.size} selected items`}
            >
              <svg width="11" height="12" viewBox="0 0 11 12" fill="none">
                <path d="M1 3h9M4 3V2h3v1M2 3l.7 7.5A.5.5 0 003.2 11h4.6a.5.5 0 00.5-.5L9 3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span style={{ fontSize: '10px', lineHeight: 1 }}>{selectedPaths.size}</span>
            </button>
          )}
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
        onClick={(e) => {
          if (e.target === e.currentTarget) onSelectionChange(new Set())
        }}
        onContextMenu={(e) => {
          // Only fire if the click is on the empty area itself, not on a child node
          if (e.target === e.currentTarget) {
            e.preventDefault()
            setCtxMenu({ x: e.clientX, y: e.clientY, node: null })
          }
        }}
      >
        {creating?.parentPath === vaultDir && renderCreateInput(0)}
        {fileTree.map((node) => renderNode(node, 0))}
        {fileTree.length === 0 && !creating && (
          <div className="sidebar-empty">No notes yet. Click + to create one.</div>
        )}
      </div>

      <div className="sidebar-footer">
        <button
          className="sidebar-btn vault-btn"
          onClick={onChangeVault}
          title="Change vault directory"
        >
          <div className="folder-icon" />
          {vaultLabel}
        </button>
        {isRepo && (
          <button
            className={`sidebar-btn sync-btn ${hasChanges ? 'has-changes' : ''} ${syncing ? 'syncing' : ''} ${isProcessing ? 'processing' : ''}`}
            onClick={onSync}
            disabled={syncing || isProcessing || !hasChanges}
            title={isProcessing ? 'Processing changes...' : hasChanges ? 'Sync to GitHub' : 'No changes to sync'}
          >
            {showSynced ? 'Synced' : 'Sync'}
          </button>
        )}
      </div>

      {/* ── Context Menu ── */}
      {ctxMenu && (
        <div
          ref={ctxMenuRef}
          className="context-menu"
          style={{ top: `${contextMenuPos.top}px`, left: `${contextMenuPos.left}px` }}
          onClick={(e) => e.stopPropagation()}
        >
          {ctxMenu.node === null ? (
            /* Empty-space context menu */
            <>
              <div
                className="context-menu-item"
                onClick={() => startCreating('note', vaultDir)}
              >
                New Note
              </div>
              <div
                className="context-menu-item"
                onClick={() => startCreating('folder', vaultDir)}
              >
                New Folder
              </div>
              {clipboardPath && (
                <>
                  <div className="context-menu-separator" />
                  <div
                    className="context-menu-item"
                    onClick={() => { onPaste(vaultDir); setCtxMenu(null) }}
                  >
                    Paste
                  </div>
                </>
              )}
            </>
          ) : ctxMenu.node.type === 'folder' ? (
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
              <div className="context-menu-separator" />
              <div
                className="context-menu-item"
                onClick={() => { onCopy(ctxMenu.node.path); setCtxMenu(null) }}
              >
                Copy
              </div>
              {clipboardPath && (
                <div
                  className="context-menu-item"
                  onClick={() => { onPaste(ctxMenu.node.path); setCtxMenu(null) }}
                >
                  Paste
                </div>
              )}
              <div className="context-menu-separator" />
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
              {selectedPaths.size > 1 && (
                <>
                  <div className="context-menu-separator" />
                  <div
                    className="context-menu-item danger"
                    onClick={() => { handleDeleteSelected(); setCtxMenu(null) }}
                  >
                    Delete Selected ({selectedPaths.size})
                  </div>
                </>
              )}
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
                onClick={() => { onOpenNoteInNewTab(ctxMenu.node.path); setCtxMenu(null) }}
              >
                Open in New Tab
              </div>
              <div className="context-menu-separator" />
              <div
                className="context-menu-item"
                onClick={() => { onCopy(ctxMenu.node.path); setCtxMenu(null) }}
              >
                Copy
              </div>
              <div className="context-menu-separator" />
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
              {selectedPaths.size > 1 && (
                <>
                  <div className="context-menu-separator" />
                  <div
                    className="context-menu-item danger"
                    onClick={() => { handleDeleteSelected(); setCtxMenu(null) }}
                  >
                    Delete Selected ({selectedPaths.size})
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
