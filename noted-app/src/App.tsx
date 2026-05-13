import { useState, useEffect, useCallback } from 'react'
import { useVault } from './hooks/useVault'
import { useGraph } from './hooks/useGraph'
import Sidebar from './components/Sidebar'
import Editor from './components/Editor'
import GraphView from './components/GraphView'
import SearchBar from './components/SearchBar'

type ViewMode = 'editor' | 'graph'

function App() {
  const {
    vaultDir,
    notes,
    activeNote,
    openNote,
    updateContent,
    createNewNote,
    deleteCurrentNote,
    changeVaultDir,
    resolveLink,
  } = useVault()

  const { nodes, links } = useGraph(notes, vaultDir)
  const [viewMode, setViewMode] = useState<ViewMode>('editor')
  const [searchVisible, setSearchVisible] = useState(false)

  const handleGraphNodeClick = useCallback((noteId: string) => {
    resolveLink(noteId)
    setViewMode('editor')
  }, [resolveLink])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+P — search
      if (e.ctrlKey && e.key === 'p') {
        e.preventDefault()
        setSearchVisible(true)
      }
      // Ctrl+N — new note
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault()
        const name = prompt('Note name:')
        if (name?.trim()) createNewNote(name.trim())
      }
      // Ctrl+G — toggle graph
      if (e.ctrlKey && e.key === 'g') {
        e.preventDefault()
        setViewMode((v) => (v === 'graph' ? 'editor' : 'graph'))
      }
      // Ctrl+Delete — delete note
      if (e.ctrlKey && e.key === 'Delete' && activeNote) {
        e.preventDefault()
        if (confirm(`Delete "${activeNote.name}"?`)) {
          deleteCurrentNote()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeNote, createNewNote, deleteCurrentNote])

  return (
    <div className="app">
      <Sidebar
        notes={notes}
        activeNotePath={activeNote?.path || null}
        onOpenNote={(path) => {
          openNote(path)
          setViewMode('editor')
        }}
        onCreateNote={createNewNote}
        onDeleteNote={activeNote ? deleteCurrentNote : undefined}
        onChangeVault={changeVaultDir}
        vaultDir={vaultDir}
        activeNoteName={activeNote?.name || null}
      />
      <div className="content">
        {/* Toolbar */}
        <div className="toolbar">
          <div className="toolbar-left">
            {activeNote && viewMode === 'editor' && (
              <span className="toolbar-title">{activeNote.name}</span>
            )}
            {viewMode === 'graph' && (
              <span className="toolbar-title">Graph View</span>
            )}
          </div>
          <div className="toolbar-right">
            <button
              className="toolbar-btn search-btn"
              onClick={() => setSearchVisible(true)}
              title="Search (Ctrl+P)"
            >
              Search
            </button>
            <button
              className={`toolbar-btn ${viewMode === 'editor' ? 'active' : ''}`}
              onClick={() => setViewMode('editor')}
              title="Editor"
            >
              Edit
            </button>
            <button
              className={`toolbar-btn ${viewMode === 'graph' ? 'active' : ''}`}
              onClick={() => setViewMode('graph')}
              title="Graph View (Ctrl+G)"
            >
              Graph
            </button>
          </div>
        </div>

        {/* Content Area */}
        {viewMode === 'editor' ? (
          activeNote ? (
            <Editor
              key={activeNote.path}
              content={activeNote.content}
              onChange={updateContent}
              noteId={activeNote.path}
              onLinkClick={resolveLink}
            />
          ) : (
            <div className="content-empty">
              <h2>Welcome to Noted</h2>
              <p>Select a note from the sidebar or create a new one</p>
              <div className="shortcuts-hint">
                <p><kbd>Ctrl+N</kbd> New note</p>
                <p><kbd>Ctrl+P</kbd> Search</p>
                <p><kbd>Ctrl+G</kbd> Graph view</p>
              </div>
            </div>
          )
        ) : (
          <GraphView
            nodes={nodes}
            links={links}
            onNodeClick={handleGraphNodeClick}
          />
        )}
      </div>

      {/* Search overlay */}
      <SearchBar
        notes={notes}
        onOpenNote={(path) => {
          openNote(path)
          setViewMode('editor')
        }}
        visible={searchVisible}
        onClose={() => setSearchVisible(false)}
      />
    </div>
  )
}

export default App
