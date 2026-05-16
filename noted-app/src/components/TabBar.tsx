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
  // For context menu only
  onNewNote: () => void
  onNewFolder: () => void
  clipboardPath: string | null
  onPaste: () => void
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
