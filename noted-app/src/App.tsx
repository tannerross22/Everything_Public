import { useState, useEffect, useCallback, useRef } from 'react'
import { useVault } from './hooks/useVault'
import { useGraph } from './hooks/useGraph'
import Sidebar from './components/Sidebar'
import Editor from './components/Editor'
import GraphView from './components/GraphView'
import SearchBar from './components/SearchBar'
import {
  loadFolderColors,
  assignFolderColor,
  isTopLevelFolder,
} from './hooks/useFolderColors'
import { loadSidebarState, saveSidebarState } from './utils/sidebarStorage'
import TabBar, { type OpenTab } from './components/TabBar'
import FindBar from './components/FindBar'

type ViewMode = 'editor' | 'graph'

function App() {
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
    resolveLink,
    refreshNotes,
    clearActiveNote,
  } = useVault()

  const { nodes, links } = useGraph(notes, vaultDir)
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
      // Delete — delete active note (only if not editing content)
      if (!isEditing && e.key === 'Delete' && activeNote) {
        e.preventDefault()
        window.api.confirm(`Delete "${activeNote.name}"?`).then((ok) => {
          if (ok) {
            closeTab(activeTabIndex)
            deleteCurrentNote()
          }
        })
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeNote, createNewNote, deleteCurrentNote, closeTab, activeTabIndex])

  return (
    <div className="app">
      <Sidebar
        fileTree={fileTree}
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
        onCollapse={handleToggleSidebarCollapse}
        style={{ width: sidebarCollapsed ? '0px' : `${sidebarWidth}px`, overflow: 'hidden' }}
        className={isResizing ? 'sidebar-resizing' : ''}
      />
      {/* Resize handle — only show when sidebar is not collapsed */}
      {!sidebarCollapsed && (
        <div
          className="resize-handle"
          onMouseDown={handleStartResize}
          title="Drag to resize sidebar"
        />
      )}

      {/* Expand button — only show when sidebar is collapsed */}
      {sidebarCollapsed && (
        <button
          className="sidebar-expand-btn"
          onClick={handleToggleSidebarCollapse}
          title="Expand sidebar"
        >
          ⟩
        </button>
      )}

      <div className="content">
        {/* Tabs — always visible so the + button is accessible */}
        <TabBar
          tabs={openTabs}
          activeIndex={activeTabIndex}
          onTabClick={switchTab}
          onTabClose={closeTab}
          onNewNote={createNoteInNewTab}
          onNewFolder={createFolderFromPrompt}
          clipboardPath={clipboardPath}
          onPaste={() => handlePaste(vaultDir)}
          viewMode={viewMode}
          onSetViewMode={setViewMode}
          onSearch={() => setSearchVisible(true)}
          onRefreshGraph={() => refreshNotes()}
        />

        {/* Content Area */}
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
    </div>
  )
}

export default App
