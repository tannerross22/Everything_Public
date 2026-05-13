import React, { useState } from 'react'

export interface OpenTab {
  path: string
  name: string
}

interface TabBarProps {
  tabs: OpenTab[]
  activeIndex: number
  onTabClick: (index: number) => void
  onTabClose: (index: number) => void
  onNewNote: () => void
  onNewFolder: () => void
  clipboardPath: string | null
  onPaste: () => void
  viewMode: 'editor' | 'graph'
  onSetViewMode: (mode: 'editor' | 'graph') => void
  onSearch: () => void
  onRefreshGraph: () => void
}

type CtxMenu = { x: number; y: number } | null

export default function TabBar({
  tabs,
  activeIndex,
  onTabClick,
  onTabClose,
  onNewNote,
  onNewFolder,
  clipboardPath,
  onPaste,
  viewMode,
  onSetViewMode,
  onSearch,
  onRefreshGraph,
}: TabBarProps) {
  const [ctxMenu, setCtxMenu] = useState<CtxMenu>(null)

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault()
    setCtxMenu({ x: e.clientX, y: e.clientY })
  }

  const closeCtx = () => setCtxMenu(null)

  return (
    <div
      className="tab-bar"
      onContextMenu={handleContextMenu}
      onClick={closeCtx}
    >
      <div className="tabs-container">
        {tabs.map((tab, index) => (
          <div
            key={tab.path}
            className={`tab ${index === activeIndex ? 'active' : ''}`}
            onClick={() => onTabClick(index)}
            onContextMenu={(e) => e.stopPropagation()}
          >
            <span className="tab-name">{tab.name}</span>
            <button
              className="tab-close"
              onClick={(e) => {
                e.stopPropagation()
                onTabClose(index)
              }}
              title="Close tab"
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <button className="tab-new" onClick={onNewNote} title="New Note">
        +
      </button>

      {/* Toolbar buttons */}
      <div className="tab-toolbar">
        <button
          className="toolbar-btn search-btn"
          onClick={onSearch}
          title="Search (Ctrl+P)"
        >
          Search
        </button>
        {viewMode === 'graph' && (
          <button
            className="toolbar-btn"
            onClick={onRefreshGraph}
            title="Refresh graph"
          >
            ↻
          </button>
        )}
        <button
          className={`toolbar-btn ${viewMode === 'editor' ? 'active' : ''}`}
          onClick={() => onSetViewMode('editor')}
          title="Editor"
        >
          Edit
        </button>
        <button
          className={`toolbar-btn ${viewMode === 'graph' ? 'active' : ''}`}
          onClick={() => onSetViewMode('graph')}
          title="Graph View (Ctrl+G)"
        >
          Graph
        </button>
      </div>

      {/* Right-click context menu */}
      {ctxMenu && (
        <div
          className="context-menu"
          style={{ top: ctxMenu.y, left: ctxMenu.x, position: 'fixed' }}
          onClick={(e) => e.stopPropagation()}
        >
          <div
            className="context-menu-item"
            onClick={() => { onNewNote(); closeCtx() }}
          >
            New Note
          </div>
          <div
            className="context-menu-item"
            onClick={() => { onNewFolder(); closeCtx() }}
          >
            New Folder
          </div>
          {clipboardPath && (
            <div
              className="context-menu-item"
              onClick={() => { onPaste(); closeCtx() }}
            >
              Paste
            </div>
          )}
        </div>
      )}
    </div>
  )
}
