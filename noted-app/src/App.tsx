import { useState, useEffect, useCallback, useRef } from 'react'
import { useVault } from './hooks/useVault'
import { useGraph } from './hooks/useGraph'
import { useModal } from './hooks/useModal'
import { useGitSync } from './hooks/useGitSync'
import Sidebar from './components/Sidebar'
import Editor from './components/Editor'
import GraphView from './components/GraphView'
import SearchBar from './components/SearchBar'
import Modal from './components/Modal'
import SettingsPage from './components/SettingsPage'
import {
  loadFolderColors,
  assignFolderColor,
  isTopLevelFolder,
} from './hooks/useFolderColors'
import { loadSidebarState, saveSidebarState } from './utils/sidebarStorage'
import TabBar, { type OpenTab } from './components/TabBar'
import FindBar from './components/FindBar'

type SortOrder = 'name-az' | 'name-za' | 'modified-new' | 'modified-old' | 'created-new' | 'created-old'

type ViewMode = 'editor' | 'graph'

function App() {
  const modal = useModal()
  const {
    vaultDir,
    notes,
    fileTree,
    activeNote,
    openNote,
    updateContent,
    createNewNote,
    deleteCurrentNote,
    changeVaultDir,
    renameNote,
    createFolder,
    deleteFolder,
    moveItem,
    resolveLink: originalResolveLink,
    refreshNotes,
    clearActiveNote,
  } = useVault()

  // Custom resolveLink that uses the modal confirm instead of API confirm
  const resolveLink = useCallback(async (linkName: string): Promise<string | undefined> => {
    const match = notes.find((n) => n.name.toLowerCase() === linkName.toLowerCase())
    if (match) {
      await openNote(match.path)
      return match.path
    } else {
      // Use modal confirm instead of window.api.confirm
      const confirmed = await modal.confirm({
        title: 'Create New Note',
        message: `Create a new note called "${linkName}"?`,
        confirmText: 'Create',
        cancelText: 'Cancel',
      })
      if (!confirmed) return undefined

      // Get the folder of the current note, or use vault root
      let targetFolder = vaultDir
      if (activeNote?.path) {
        const sep = activeNote.path.includes('\\') ? '\\' : '/'
        const lastSepIndex = activeNote.path.lastIndexOf(sep)
        targetFolder = activeNote.path.substring(0, lastSepIndex)
      }

      const newPath = await createNewNote(linkName, targetFolder)
      if (newPath) await openNote(newPath)
      return newPath
    }
  }, [notes, openNote, modal, vaultDir, activeNote?.path, createNewNote])

  const { nodes, links } = useGraph(notes, vaultDir)
  const gitSync = useGitSync(vaultDir)
  const [viewMode, setViewMode] = useState<ViewMode>('editor')
  const [searchVisible, setSearchVisible] = useState(false)
  const [folderColors, setFolderColors] = useState<Record<string, string>>(() => loadFolderColors())
  const [promptVisible, setPromptVisible] = useState(false)
  const [promptValue, setPromptValue] = useState('')
  const [promptType, setPromptType] = useState<'note' | 'folder'>('note')
  const [openTabs, setOpenTabs] = useState<OpenTab[]>([])
  const [activeTabIndex, setActiveTabIndex] = useState(-1)
  const [clipboardPath, setClipboardPath] = useState<string | null>(null)
  const [findVisible, setFindVisible] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [sortOrder, setSortOrder] = useState<SortOrder>('name-az')
  const [sidebarSelectedPaths, setSidebarSelectedPaths] = useState<Set<string>>(new Set())
  const [isMaximized, setIsMaximized] = useState(false)
  const editorContainerRef = useRef<HTMLDivElement>(null)

  // Sidebar resizing and collapsing
  const { width: savedWidth, collapsed: savedCollapsed } = loadSidebarState()
  const [sidebarWidth, setSidebarWidth] = useState(savedWidth)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(savedCollapsed)
  const [isResizing, setIsResizing] = useState(false)
  const resizeRef = useRef<{ startX: number; startWidth: number; currentWidth: number } | null>(null)

  // Git setup modal
  const [isGitRepo, setIsGitRepo] = useState(false)
  const [showGitSetup, setShowGitSetup] = useState(false)
  const [gitUrl, setGitUrl] = useState('')
  const [gitSetupLoading, setGitSetupLoading] = useState(false)
  const [gitSetupError, setGitSetupError] = useState<string | null>(null)

  // Whether a tab is selected (activeNote from useVault has the content)
  const hasActiveTab = activeTabIndex >= 0 && activeTabIndex < openTabs.length

  // Clear sidebar selection whenever the vault changes
  useEffect(() => {
    setSidebarSelectedPaths(new Set())
  }, [vaultDir])

  // Auto-assign colors whenever the file tree changes (e.g. vault opened, folder created)
  useEffect(() => {
    if (!vaultDir) return
    const updated = { ...loadFolderColors() }
    let changed = false
    for (const node of fileTree) {
      if (node.type === 'folder' && isTopLevelFolder(node.path, vaultDir) && !updated[node.path]) {
        updated[node.path] = assignFolderColor(node.path)
        changed = true
      }
    }
    if (changed) setFolderColors(updated)
  }, [fileTree, vaultDir])

  // ── Tab operations ──
  // Every note open — whether from sidebar click, right-click "Open in New Tab",
  // search, or graph — goes through this so there's always a tab for it.
  const openNoteInTab = useCallback(async (path: string) => {
    // Close find bar when switching notes
    setFindVisible(false)
    // Load the note content first
    await openNote(path)

    // Derive name from the loaded notes list (may have just been refreshed)
    const name = notes.find((n) => n.path === path)?.name
      ?? path.split(/[/\\]/).pop()?.replace(/\.md$/i, '')
      ?? 'Untitled'

    setOpenTabs((prev) => {
      const existingIndex = prev.findIndex((t) => t.path === path)
      if (existingIndex >= 0) {
        setActiveTabIndex(existingIndex)
        return prev
      }
      const next = [...prev, { path, name }]
      setActiveTabIndex(next.length - 1)
      return next
    })

    setViewMode('editor')
  }, [notes, openNote])

  const switchTab = useCallback((index: number) => {
    if (index >= 0 && index < openTabs.length) {
      setActiveTabIndex(index)
      openNote(openTabs[index].path)
    }
  }, [openTabs, openNote])

  const closeTab = useCallback((index: number) => {
    const newTabs = openTabs.filter((_, i) => i !== index)
    setOpenTabs(newTabs)

    // Update active index
    if (index === activeTabIndex) {
      // Closing the active tab
      if (newTabs.length === 0) {
        setActiveTabIndex(-1)
        clearActiveNote()
      } else if (index >= newTabs.length) {
        // Closed tab was at the end, switch to previous
        setActiveTabIndex(newTabs.length - 1)
        openNote(newTabs[newTabs.length - 1].path)
      } else {
        // Closed tab was in the middle, stay on same index (which is now the next tab)
        setActiveTabIndex(index)
        openNote(newTabs[index].path)
      }
    } else if (index < activeTabIndex) {
      // Closing a tab before the active one, shift index left
      setActiveTabIndex(activeTabIndex - 1)
    }
  }, [openTabs, activeTabIndex, openNote, clearActiveNote])

  const createNoteInNewTab = useCallback(() => {
    setPromptType('note')
    setPromptValue('')
    setPromptVisible(true)
  }, [])

  const createFolderFromPrompt = useCallback(() => {
    setPromptType('folder')
    setPromptValue('')
    setPromptVisible(true)
  }, [])

  const handleGraphNodeClick = useCallback(async (noteId: string) => {
    const notePath = await resolveLink(noteId)
    if (notePath) {
      await openNoteInTab(notePath)
    }
  }, [resolveLink, openNoteInTab])

  const handleCreateFolder = useCallback((fullPath: string) => {
    createFolder(fullPath)
    if (vaultDir && isTopLevelFolder(fullPath, vaultDir)) {
      const color = assignFolderColor(fullPath)
      setFolderColors((prev) => ({ ...prev, [fullPath]: color }))
    }
  }, [createFolder, vaultDir])

  const handlePromptSubmit = async () => {
    if (promptValue.trim()) {
      if (promptType === 'note') {
        const filePath = await createNewNote(promptValue.trim())
        setPromptVisible(false)
        setPromptValue('')
        if (filePath) await openNoteInTab(filePath)
      } else {
        const sep = vaultDir.includes('\\') ? '\\' : '/'
        handleCreateFolder(vaultDir + sep + promptValue.trim())
        setPromptVisible(false)
        setPromptValue('')
      }
    }
  }

  const handlePromptKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handlePromptSubmit()
    }
    if (e.key === 'Escape') {
      setPromptVisible(false)
      setPromptValue('')
    }
  }

  const handlePaste = useCallback(async (destFolder: string) => {
    if (!clipboardPath) return
    await window.api.copyItem(clipboardPath, destFolder)
    await refreshNotes()
  }, [clipboardPath, refreshNotes])

  // Delete multiple selected sidebar items
  const handleDeleteItems = useCallback(async (items: Array<{ path: string; type: 'file' | 'folder' }>) => {
    if (items.length === 0) return

    const count = items.length
    const confirmed = await modal.confirm({
      title: `Delete ${count} Item${count > 1 ? 's' : ''}`,
      message: `Delete ${count} selected item${count > 1 ? 's' : ''}? This cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      isDangerous: true,
    })
    if (!confirmed) return

    // Skip items whose parent folder is also being deleted
    const folderPaths = items.filter((i) => i.type === 'folder').map((i) => i.path)
    const toDelete = items.filter(
      (item) =>
        !folderPaths.some(
          (fp) =>
            item.path !== fp &&
            (item.path.startsWith(fp + '\\') || item.path.startsWith(fp + '/'))
        )
    )

    for (const item of toDelete) {
      try {
        if (item.type === 'folder') {
          await window.api.deleteFolder(item.path)
        } else {
          await window.api.deleteNote(item.path)
        }
      } catch (e) {
        console.error('[handleDeleteItems] Failed to delete', item.path, e)
      }
    }

    // Determine which tab paths are now gone (deleted directly or inside a deleted folder)
    const isGone = (path: string) =>
      toDelete.some((i) => i.path === path) ||
      folderPaths.some((fp) => path.startsWith(fp + '\\') || path.startsWith(fp + '/'))

    const currentTab = openTabs[activeTabIndex]
    const newTabs = openTabs.filter((t) => !isGone(t.path))
    setOpenTabs(newTabs)

    if (newTabs.length === 0) {
      setActiveTabIndex(-1)
      clearActiveNote()
    } else if (currentTab && isGone(currentTab.path)) {
      const newIdx = Math.min(activeTabIndex, newTabs.length - 1)
      setActiveTabIndex(newIdx)
      openNote(newTabs[newIdx].path)
    } else if (currentTab) {
      const newIdx = newTabs.findIndex((t) => t.path === currentTab.path)
      if (newIdx >= 0) setActiveTabIndex(newIdx)
    }

    setSidebarSelectedPaths(new Set())
    await refreshNotes()
  }, [modal, openTabs, activeTabIndex, openNote, clearActiveNote, refreshNotes])

  // Sort file tree based on sort order, with folders always appearing first
  const sortFileTree = useCallback((nodes: typeof fileTree, order: SortOrder): typeof fileTree => {
    const sortComparator = (a: typeof fileTree[0], b: typeof fileTree[0]): number => {
      switch (order) {
        case 'name-az':
          return a.name.localeCompare(b.name)
        case 'name-za':
          return b.name.localeCompare(a.name)
        case 'modified-new':
          return (b.modifiedAt ?? 0) - (a.modifiedAt ?? 0)
        case 'modified-old':
          return (a.modifiedAt ?? 0) - (b.modifiedAt ?? 0)
        case 'created-new':
          return (b.modifiedAt ?? 0) - (a.modifiedAt ?? 0)
        case 'created-old':
          return (a.modifiedAt ?? 0) - (b.modifiedAt ?? 0)
        default:
          return 0
      }
    }

    // Separate folders and files
    const folders = nodes.filter((node) => node.type === 'folder')
    const files = nodes.filter((node) => node.type === 'file')

    // Sort each group
    const sortedFolders = folders
      .sort((a, b) => a.name.localeCompare(b.name)) // Folders always sorted A-Z by name
      .map((node) => ({
        ...node,
        children: node.children ? sortFileTree(node.children, order) : undefined,
      }))

    const sortedFiles = files
      .sort(sortComparator) // Files sorted by selected order
      .map((node) => ({
        ...node,
        children: node.children ? sortFileTree(node.children, order) : undefined,
      }))

    // Return folders first, then files
    return [...sortedFolders, ...sortedFiles]
  }, [])

  // Apply sort order to file tree
  const sortedFileTree = sortFileTree(fileTree, sortOrder)

  // Sidebar resize handlers
  const handleStartResize = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    resizeRef.current = { startX: e.clientX, startWidth: sidebarWidth, currentWidth: sidebarWidth }

    const handleResizeMove = (moveEvent: MouseEvent) => {
      if (!resizeRef.current) return
      const delta = moveEvent.clientX - resizeRef.current.startX
      const newWidth = Math.max(180, Math.min(500, resizeRef.current.startWidth + delta))
      resizeRef.current.currentWidth = newWidth
      setSidebarWidth(newWidth)
    }

    const handleResizeEnd = () => {
      setIsResizing(false)
      if (resizeRef.current) {
        // Save the final width tracked during the resize
        saveSidebarState(resizeRef.current.currentWidth, sidebarCollapsed)
      }
      window.removeEventListener('mousemove', handleResizeMove)
      window.removeEventListener('mouseup', handleResizeEnd)
      resizeRef.current = null
    }

    window.addEventListener('mousemove', handleResizeMove)
    window.addEventListener('mouseup', handleResizeEnd)
  }

  const handleToggleSidebarCollapse = useCallback(() => {
    const newCollapsed = !sidebarCollapsed
    setSidebarCollapsed(newCollapsed)
    saveSidebarState(sidebarWidth, newCollapsed)
  }, [sidebarCollapsed, sidebarWidth])

  // Check if vault is a git repo when vaultDir changes
  useEffect(() => {
    if (!vaultDir) {
      console.log('[Git Setup] No vaultDir yet')
      return
    }

    console.log('[Git Setup] Checking if vaultDir is a git repo:', vaultDir)

    const checkGitRepo = async () => {
      try {
        console.log('[Git Setup] Calling window.api.isGitRepo...')
        const isRepo = await window.api.isGitRepo(vaultDir)
        console.log('[Git Setup] isGitRepo result:', isRepo)
        setIsGitRepo(isRepo)
        // If not a git repo, show setup modal
        if (!isRepo) {
          console.log('[Git Setup] Not a git repo, showing setup modal')
          setShowGitSetup(true)
          setGitUrl('')
          setGitSetupError(null)
        } else {
          console.log('[Git Setup] Already a git repo')
        }
      } catch (error) {
        console.error('[Git Setup] Error checking git repo:', error)
        // Treat errors as "not a repo" and show setup modal
        setIsGitRepo(false)
        setShowGitSetup(true)
        setGitUrl('')
        setGitSetupError(null)
      }
    }

    checkGitRepo()
  }, [vaultDir])

  // Handle Git setup
  const handleGitSetup = async () => {
    if (!gitUrl.trim()) {
      setGitSetupError('Please enter a GitHub repository URL')
      return
    }

    // Basic URL validation
    const urlPattern = /^https:\/\/github\.com\/[\w-]+\/[\w.-]+(?:\.git)?$/i
    if (!urlPattern.test(gitUrl.trim())) {
      setGitSetupError('Please enter a valid GitHub repository URL (e.g., https://github.com/username/repo or https://github.com/username/repo.git)')
      return
    }

    setGitSetupLoading(true)
    setGitSetupError(null)

    try {
      // Step 1: Initialize git repo
      await window.api.gitInit(vaultDir)

      // Step 2: Add remote
      const remoteUrl = gitUrl.trim().endsWith('.git') ? gitUrl.trim() : `${gitUrl.trim()}.git`
      await window.api.gitAddRemote(vaultDir, 'origin', remoteUrl)

      // Step 3: Create initial commit
      await window.api.gitInitialCommit(vaultDir, 'Initial commit from Noted')

      // Setup complete
      setIsGitRepo(true)
      setShowGitSetup(false)
      setGitUrl('')
      setGitSetupError(null)

      // Refresh notes to update sidebar git status
      await refreshNotes()
    } catch (error: any) {
      console.error('Git setup error:', error)
      const errorMessage = error?.message || 'Failed to set up Git repository'
      setGitSetupError(errorMessage)
    } finally {
      setGitSetupLoading(false)
    }
  }

  const handleGitSetupKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !gitSetupLoading) {
      handleGitSetup()
    }
    if (e.key === 'Escape') {
      setShowGitSetup(false)
      setGitUrl('')
      setGitSetupError(null)
    }
  }

  // Refresh note metadata (and thus graph links) whenever the user opens graph view
  useEffect(() => {
    if (viewMode === 'graph') refreshNotes()
  }, [viewMode])

  // Sync maximized state on mount and window resize
  useEffect(() => {
    window.api.windowIsMaximized().then(setIsMaximized)
  }, [])

  // Listen for menu events
  useEffect(() => {
    const unsubNewNote = window.api.onMenuNewNote(() => {
      setPromptType('note')
      setPromptValue('')
      setPromptVisible(true)
    })

    const unsubOpenSettings = window.api.onMenuOpenSettings(() => {
      setShowSettings(true)
    })

    const unsubSetSortOrder = window.api.onMenuSetSortOrder((order: string) => {
      setSortOrder(order as SortOrder)
    })

    return () => {
      unsubNewNote()
      unsubOpenSettings()
      unsubSetSortOrder()
    }
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger destructive shortcuts if user is typing in an input or the editor
      const target = e.target as HTMLElement
      const isEditing = target.tagName === 'INPUT'
        || target.tagName === 'TEXTAREA'
        || target.isContentEditable

      // Ctrl+P — search notes
      if (e.ctrlKey && e.key === 'p') {
        e.preventDefault()
        setSearchVisible(true)
      }
      // Ctrl+F — find in current note
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        setFindVisible(true)
      }
      // Ctrl+N — new note (show modal prompt)
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault()
        setPromptType('note')
        setPromptValue('')
        setPromptVisible(true)
      }
      // Ctrl+G — toggle graph
      if (e.ctrlKey && e.key === 'g') {
        e.preventDefault()
        setViewMode((v) => (v === 'graph' ? 'editor' : 'graph'))
      }
      // Delete — multi-select if 2+ sidebar items selected, otherwise delete active note
      if (!isEditing && e.key === 'Delete') {
        if (sidebarSelectedPaths.size > 1) {
          e.preventDefault()
          // Build items list from the sorted file tree
          const allNodes: typeof fileTree = []
          const flatten = (nodes: typeof fileTree) => {
            for (const n of nodes) { allNodes.push(n); if (n.children) flatten(n.children) }
          }
          flatten(sortedFileTree)
          const pathTypeMap = new Map(allNodes.map((n) => [n.path, n.type as 'file' | 'folder']))
          const items = Array.from(sidebarSelectedPaths).map((p) => ({
            path: p,
            type: pathTypeMap.get(p) ?? ('file' as const),
          }))
          handleDeleteItems(items)
        } else if (activeNote) {
          e.preventDefault()
          modal.confirm({
            title: 'Delete Note',
            message: `Delete "${activeNote.name}"? This cannot be undone.`,
            confirmText: 'Delete',
            cancelText: 'Cancel',
            isDangerous: true,
          }).then((ok) => {
            if (ok) {
              closeTab(activeTabIndex)
              deleteCurrentNote()
            }
          })
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeNote, createNewNote, deleteCurrentNote, closeTab, activeTabIndex, sidebarSelectedPaths, handleDeleteItems, sortedFileTree, modal])

  return (
    <div className="app">

      {/* ── Custom Title Bar (replaces native Electron chrome) ── */}
      <div className="title-bar">
        {/* Sidebar toggle — left rail section */}
        <button
          className="title-rail-btn"
          onClick={handleToggleSidebarCollapse}
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="1" y="3" width="14" height="1.5" rx="0.75" fill="currentColor"/>
            <rect x="1" y="7.25" width="14" height="1.5" rx="0.75" fill="currentColor"/>
            <rect x="1" y="11.5" width="14" height="1.5" rx="0.75" fill="currentColor"/>
          </svg>
        </button>

        {/* Tabs area — draggable */}
        <div className="title-tabs">
          <TabBar
            tabs={openTabs}
            activeIndex={activeTabIndex}
            onTabClick={switchTab}
            onTabClose={closeTab}
            onNewNote={createNoteInNewTab}
            onNewFolder={createFolderFromPrompt}
            clipboardPath={clipboardPath}
            onPaste={() => handlePaste(vaultDir)}
          />
        </div>

        {/* Right controls — action buttons + window chrome */}
        <div className="title-controls">
          <button
            className="title-action-btn"
            onClick={createNoteInNewTab}
            title="New Note (Ctrl+N)"
          >
            +
          </button>
          <button
            className="title-action-btn"
            onClick={() => setSearchVisible(true)}
            title="Search (Ctrl+P)"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="5.5" cy="5.5" r="4" stroke="currentColor" strokeWidth="1.4"/>
              <line x1="8.7" y1="8.7" x2="13" y2="13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
          </button>
          <button
            className={`title-action-btn ${viewMode === 'graph' ? 'active' : ''}`}
            onClick={() => setViewMode(v => v === 'graph' ? 'editor' : 'graph')}
            title="Graph View (Ctrl+G)"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="3" r="2" stroke="currentColor" strokeWidth="1.3"/>
              <circle cx="2.5" cy="11" r="1.8" stroke="currentColor" strokeWidth="1.3"/>
              <circle cx="11.5" cy="11" r="1.8" stroke="currentColor" strokeWidth="1.3"/>
              <line x1="5.7" y1="4.6" x2="3.3" y2="9.3" stroke="currentColor" strokeWidth="1.2"/>
              <line x1="8.3" y1="4.6" x2="10.7" y2="9.3" stroke="currentColor" strokeWidth="1.2"/>
              <line x1="4.3" y1="11" x2="9.7" y2="11" stroke="currentColor" strokeWidth="1.2"/>
            </svg>
          </button>

          {/* Window controls */}
          <div className="win-ctrl-sep" />
          <button
            className="win-ctrl"
            onClick={() => window.api.windowMinimize()}
            title="Minimize"
          >
            <svg width="10" height="10" viewBox="0 0 10 10"><line x1="1" y1="5" x2="9" y2="5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
          </button>
          <button
            className="win-ctrl"
            onClick={() => { window.api.windowToggleMaximize(); setIsMaximized(m => !m) }}
            title={isMaximized ? 'Restore' : 'Maximize'}
          >
            {isMaximized ? (
              <svg width="10" height="10" viewBox="0 0 10 10"><rect x="3" y="1" width="6" height="6" rx="0.5" stroke="currentColor" strokeWidth="1.3" fill="none"/><path d="M1 3v5.5A0.5 0.5 0 001.5 9H7" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>
            ) : (
              <svg width="10" height="10" viewBox="0 0 10 10"><rect x="1" y="1" width="8" height="8" rx="0.5" stroke="currentColor" strokeWidth="1.3" fill="none"/></svg>
            )}
          </button>
          <button
            className="win-ctrl win-ctrl-close"
            onClick={() => window.api.windowClose()}
            title="Close"
          >
            <svg width="10" height="10" viewBox="0 0 10 10"><line x1="1.5" y1="1.5" x2="8.5" y2="8.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/><line x1="8.5" y1="1.5" x2="1.5" y2="8.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
          </button>
        </div>
      </div>

      {/* ── Body Row ── */}
      <div className="body-row">

        {/* Persistent left rail */}
        <div className="app-rail">
          {gitSync.isRepo && (
            <button
              className={`rail-sync-btn ${gitSync.hasChanges ? 'has-changes' : ''} ${gitSync.syncing ? 'syncing' : ''} ${gitSync.isProcessing ? 'processing' : ''} ${gitSync.showSynced ? 'synced' : ''}`}
              onClick={gitSync.handleSync}
              disabled={gitSync.syncing || gitSync.isProcessing || !gitSync.hasChanges}
              title={gitSync.isProcessing ? 'Processing...' : gitSync.hasChanges ? 'Sync to GitHub' : 'Up to date'}
            />
          )}
        </div>

        {/* Sidebar + resize handle + content */}
        <div className="body-content">
          {!sidebarCollapsed && (
            <Sidebar
              fileTree={sortedFileTree}
              activeNotePath={activeNote?.path || null}
              activeNoteName={activeNote?.name || null}
              onOpenNote={openNoteInTab}
              onOpenNoteInNewTab={openNoteInTab}
              onCreateNote={async (name: string, folderPath?: string) => {
                const filePath = await createNewNote(name, folderPath)
                if (filePath) await openNoteInTab(filePath)
              }}
              onCreateFolder={handleCreateFolder}
              onDeleteFolder={deleteFolder}
              onDeleteNote={activeNote ? deleteCurrentNote : undefined}
              onMoveItem={moveItem}
              onChangeVault={changeVaultDir}
              onRenameNote={renameNote}
              vaultDir={vaultDir}
              folderColors={folderColors}
              clipboardPath={clipboardPath}
              onCopy={setClipboardPath}
              onPaste={handlePaste}
              onConfirm={modal.confirm}
              isRepo={gitSync.isRepo}
              hasChanges={gitSync.hasChanges}
              syncing={gitSync.syncing}
              isProcessing={gitSync.isProcessing}
              showSynced={gitSync.showSynced}
              onSync={gitSync.handleSync}
              selectedPaths={sidebarSelectedPaths}
              onSelectionChange={setSidebarSelectedPaths}
              onDeleteItems={handleDeleteItems}
              style={{ width: `${sidebarWidth}px` }}
              className={isResizing ? 'sidebar-resizing' : ''}
            />
          )}

          {/* Resize handle */}
          {!sidebarCollapsed && (
            <div
              className="resize-handle"
              onMouseDown={handleStartResize}
              title="Drag to resize sidebar"
            />
          )}

          {/* Main content */}
          <div className="content">
            {viewMode === 'editor' ? (
              activeNote ? (
                <div ref={editorContainerRef} className="editor-area">
                  <FindBar
                    visible={findVisible}
                    onClose={() => setFindVisible(false)}
                    containerEl={editorContainerRef.current}
                  />
                  <Editor
                    key={activeNote.path}
                    content={activeNote.content}
                    onChange={updateContent}
                    noteId={activeNote.path}
                    vaultDir={vaultDir}
                    onLinkClick={async (linkName: string) => {
                      const notePath = await resolveLink(linkName)
                      if (notePath) await openNoteInTab(notePath)
                    }}
                  />
                </div>
              ) : (
                <div className="content-empty">
                  <h2>Welcome to Noted</h2>
                  <p>Select a note from the sidebar or create a new one</p>
                  <div className="shortcuts-hint">
                    <p><kbd>Ctrl+N</kbd> New note</p>
                    <p><kbd>Ctrl+P</kbd> Search</p>
                    <p><kbd>Ctrl+F</kbd> Find in note</p>
                    <p><kbd>Ctrl+G</kbd> Graph view</p>
                  </div>
                </div>
              )
            ) : (
              <GraphView
                nodes={nodes}
                links={links}
                onNodeClick={handleGraphNodeClick}
                folderColors={folderColors}
                vaultDir={vaultDir}
              />
            )}
          </div>
        </div>
      </div>

      {/* Prompt for new note name */}
      {promptVisible && (
        <div className="modal-overlay" onClick={() => { setPromptVisible(false); setPromptValue('') }}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h2>{promptType === 'note' ? 'New Note' : 'New Folder'}</h2>
            <input
              type="text"
              className="modal-input"
              placeholder={promptType === 'note' ? 'Note name...' : 'Folder name...'}
              value={promptValue}
              onChange={(e) => setPromptValue(e.target.value)}
              onKeyDown={handlePromptKeyDown}
              autoFocus
            />
            <div className="modal-buttons">
              <button
                className="modal-btn cancel"
                onClick={() => { setPromptVisible(false); setPromptValue('') }}
              >
                Cancel
              </button>
              <button
                className="modal-btn submit"
                onClick={handlePromptSubmit}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Git Setup Modal */}
      {showGitSetup && !isGitRepo && (
        <div className="modal-overlay" onClick={() => { setShowGitSetup(false); setGitUrl(''); setGitSetupError(null) }}>
          <div className="modal-dialog git-setup-dialog" onClick={(e) => e.stopPropagation()}>
            <h2>Set Up Git Repository</h2>
            <p className="git-setup-description">
              This folder is not a Git repository. To use sync features, connect it to a GitHub repository.
            </p>
            <input
              type="text"
              className="modal-input"
              placeholder="GitHub repository URL (https://github.com/username/repo)"
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              onKeyDown={handleGitSetupKeyDown}
              disabled={gitSetupLoading}
              autoFocus
            />
            {gitSetupError && (
              <div className="git-setup-error">
                {gitSetupError}
              </div>
            )}
            <div className="modal-buttons">
              <button
                className="modal-btn cancel"
                onClick={() => { setShowGitSetup(false); setGitUrl(''); setGitSetupError(null) }}
                disabled={gitSetupLoading}
              >
                Skip for Now
              </button>
              <button
                className="modal-btn submit"
                onClick={handleGitSetup}
                disabled={gitSetupLoading}
              >
                {gitSetupLoading ? 'Setting Up...' : 'Set Up Repository'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Search overlay */}
      <SearchBar
        notes={notes}
        onOpenNote={openNoteInTab}
        visible={searchVisible}
        onClose={() => setSearchVisible(false)}
      />

      {/* Custom Modal Dialog */}
      {modal.isOpen && modal.config && (
        <Modal
          title={modal.config.title}
          message={modal.config.message}
          confirmText={modal.config.confirmText}
          cancelText={modal.config.cancelText}
          isDangerous={modal.config.isDangerous}
          onConfirm={modal.handleConfirm}
          onCancel={modal.handleCancel}
        />
      )}

      {/* Settings Panel */}
      {showSettings && (
        <SettingsPage onClose={() => setShowSettings(false)} />
      )}
    </div>
  )
}

export default App
