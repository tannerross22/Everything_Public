import { useState, useEffect, useCallback, useRef } from 'react'
import type { NoteFile, NoteContent, FileTreeNode } from '../types'

export function useVault() {
  const [vaultDir, setVaultDir] = useState<string>('')
  const [notes, setNotes] = useState<NoteFile[]>([])
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([])
  const [activeNote, setActiveNote] = useState<NoteContent | null>(null)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load vault directory on mount
  useEffect(() => {
    window.api.getVaultDir().then((dir) => {
      setVaultDir(dir)
    })
  }, [])

  // Fetch flat list + tree whenever vault dir changes
  const refreshNotes = useCallback(async () => {
    if (!vaultDir) return
    const [noteList, tree] = await Promise.all([
      window.api.listNotes(vaultDir),
      window.api.buildFileTree(vaultDir),
    ])
    setNotes(noteList)
    setFileTree(tree)
  }, [vaultDir])

  useEffect(() => {
    refreshNotes()
  }, [refreshNotes])

  // Listen for external file changes
  useEffect(() => {
    const unsubscribe = window.api.onFilesChanged(() => {
      refreshNotes()
      if (activeNote) {
        window.api.readNote(activeNote.path).then((content) => {
          setActiveNote((prev) => prev ? { ...prev, content } : null)
        }).catch(() => {
          setActiveNote(null)
        })
      }
    })
    return unsubscribe
  }, [refreshNotes, activeNote?.path])

  // Open a note
  const openNote = useCallback(async (filePath: string) => {
    const content = await window.api.readNote(filePath)
    const name = filePath.split(/[/\\]/).pop()?.replace(/\.md$/, '') || ''
    setActiveNote({ name, path: filePath, content })
    window.api.setTitle(`Noted - ${name}`)
  }, [])

  // Save note with debouncing
  const saveNote = useCallback((filePath: string, content: string) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(async () => {
      await window.api.writeNote(filePath, content)
    }, 500)
  }, [])

  // Update content in state and trigger debounced save
  const updateContent = useCallback((content: string) => {
    if (!activeNote) return
    setActiveNote((prev) => prev ? { ...prev, content } : null)
    saveNote(activeNote.path, content)
  }, [activeNote?.path, saveNote])

  // Create a new note — optionally inside a folder
  const createNewNote = useCallback(async (name: string, folderPath?: string) => {
    if (!vaultDir || !name.trim()) return
    const targetDir = folderPath ?? vaultDir
    const filePath = await window.api.createNote(targetDir, name.trim())
    await refreshNotes()
    await openNote(filePath)
  }, [vaultDir, refreshNotes, openNote])

  // Delete the currently active note
  const deleteCurrentNote = useCallback(async () => {
    if (!activeNote) return
    await window.api.deleteNote(activeNote.path)
    setActiveNote(null)
    window.api.setTitle('Noted')
    await refreshNotes()
  }, [activeNote, refreshNotes])

  // Change vault directory
  const changeVaultDir = useCallback(async () => {
    const newDir = await window.api.selectVaultDir()
    if (newDir) {
      setVaultDir(newDir)
      setActiveNote(null)
      window.api.setTitle('Noted')
    }
  }, [])

  // Rename a note and update all wikilink references
  const renameNote = useCallback(async (oldPath: string, newName: string) => {
    if (!vaultDir || !newName.trim()) return
    try {
      const result = await window.api.renameNote(vaultDir, oldPath, newName)
      if (activeNote?.path === oldPath) {
        setActiveNote((prev) => prev ? { ...prev, path: result.newPath, name: newName } : null)
      }
      await refreshNotes()
      return result
    } catch (error) {
      console.error('Failed to rename note:', error)
      throw error
    }
  }, [vaultDir, activeNote?.path, refreshNotes])

  // Create a folder at the given full path
  const createFolder = useCallback(async (fullPath: string) => {
    await window.api.createFolder(fullPath)
    await refreshNotes()
  }, [refreshNotes])

  // Delete a folder and all its contents
  const deleteFolder = useCallback(async (folderPath: string) => {
    await window.api.deleteFolder(folderPath)
    // Clear active note if it lived inside the deleted folder
    if (activeNote) {
      const sep = folderPath.includes('\\') ? '\\' : '/'
      if (activeNote.path.startsWith(folderPath + sep)) {
        setActiveNote(null)
        window.api.setTitle('Noted')
      }
    }
    await refreshNotes()
  }, [activeNote?.path, refreshNotes])

  // Move a file or folder to a new parent folder
  const moveItem = useCallback(async (oldPath: string, newFolderPath: string) => {
    await window.api.moveNote(oldPath, newFolderPath)
    await refreshNotes()
  }, [refreshNotes])

  // Resolve a wiki link — open existing note or create new one
  const resolveLink = useCallback(async (linkName: string) => {
    const match = notes.find((n) => n.name.toLowerCase() === linkName.toLowerCase())
    if (match) {
      await openNote(match.path)
    } else {
      await createNewNote(linkName)
    }
  }, [notes, openNote, createNewNote])

  return {
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
  }
}
