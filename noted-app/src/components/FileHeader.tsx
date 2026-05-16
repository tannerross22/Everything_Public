import { useRef, useEffect, useState } from 'react'
import '../styles/FileHeader.css'

type SortOrder = 'name-az' | 'name-za' | 'modified-new' | 'modified-old' | 'created-new' | 'created-old'

interface FileHeaderProps {
  sortOrder: SortOrder
  onSortChange: (order: SortOrder) => void
  onCreateNote: () => void
  onOpenSettings: () => void
}

export default function FileHeader({
  sortOrder,
  onSortChange,
  onCreateNote,
  onOpenSettings,
}: FileHeaderProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [showSortSubmenu, setShowSortSubmenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const sortMenuRef = useRef<HTMLDivElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false)
        setShowSortSubmenu(false)
      }
    }
    window.addEventListener('click', handleClickOutside)
    return () => window.removeEventListener('click', handleClickOutside)
  }, [])

  const handleSortChange = (order: SortOrder) => {
    onSortChange(order)
    setShowMenu(false)
    setShowSortSubmenu(false)
  }

  const getSortLabel = () => {
    const labels: Record<SortOrder, string> = {
      'name-az': 'File name (A to Z)',
      'name-za': 'File name (Z to A)',
      'modified-new': 'Modified time (new to old)',
      'modified-old': 'Modified time (old to new)',
      'created-new': 'Created time (new to old)',
      'created-old': 'Created time (old to new)',
    }
    return labels[sortOrder]
  }

  return (
    <div className="file-header" ref={menuRef}>
      <button className="file-header-btn" onClick={() => setShowMenu(!showMenu)}>
        <span className="file-header-label">Files</span>
        <span className="file-header-icon">⋯</span>
      </button>

      {showMenu && (
        <div className="file-header-menu">
          <button
            className="file-header-menu-item"
            onClick={() => {
              onCreateNote()
              setShowMenu(false)
            }}
          >
            <span className="menu-icon">+</span>
            <span className="menu-label">New Note</span>
          </button>

          <button
            className="file-header-menu-item"
            onClick={() => {
              onOpenSettings()
              setShowMenu(false)
            }}
          >
            <span className="menu-icon">⚙️</span>
            <span className="menu-label">Settings</span>
          </button>

          <div className="file-header-menu-divider" />

          <div className="file-header-menu-item sort-submenu-trigger" ref={sortMenuRef}>
            <button
              className="sort-trigger-btn"
              onClick={() => setShowSortSubmenu(!showSortSubmenu)}
            >
              <span className="menu-icon">↕️</span>
              <span className="menu-label">Sort</span>
              <span className="submenu-arrow">›</span>
            </button>

            {showSortSubmenu && (
              <div className="sort-submenu">
                <button
                  className={`sort-option ${sortOrder === 'name-az' ? 'active' : ''}`}
                  onClick={() => handleSortChange('name-az')}
                >
                  File name (A to Z)
                </button>
                <button
                  className={`sort-option ${sortOrder === 'name-za' ? 'active' : ''}`}
                  onClick={() => handleSortChange('name-za')}
                >
                  File name (Z to A)
                </button>
                <button
                  className={`sort-option ${sortOrder === 'modified-new' ? 'active' : ''}`}
                  onClick={() => handleSortChange('modified-new')}
                >
                  Modified time (new to old)
                </button>
                <button
                  className={`sort-option ${sortOrder === 'modified-old' ? 'active' : ''}`}
                  onClick={() => handleSortChange('modified-old')}
                >
                  Modified time (old to new)
                </button>
                <button
                  className={`sort-option ${sortOrder === 'created-new' ? 'active' : ''}`}
                  onClick={() => handleSortChange('created-new')}
                >
                  Created time (new to old)
                </button>
                <button
                  className={`sort-option ${sortOrder === 'created-old' ? 'active' : ''}`}
                  onClick={() => handleSortChange('created-old')}
                >
                  Created time (old to new)
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
