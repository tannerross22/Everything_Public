import { useState, useEffect, useCallback, useRef } from 'react'
import type { NoteFile, NoteContent } from '../types'

export function useVault() {
  const [vaultDir, setVaultDir] = useState<string>('')
  const [notes, setNotes] = useState<NoteFile[]>([])
  const [activeNote, setActiveNote] = useState<NoteContent | null>(null)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load vault directory on mount
  useEffect(() => {
    window.api.getVaultDir().then((dir) => {
      setVaultDir(dir)
    })
  }, [])

  // Fetch notes whenever vault dir changes
  const refreshNotes = useCallback(async () => {
    if (!vaultDir) return
    const noteList = await window.api.listNotes(vaultDir)
    setNotes(noteList)
  }, [vaultDir])

  useEffect(() => {
    refreshNotes()
  }, [refreshNotes])

  // Listen for external file changes
  useEffect(() => {
    const unsubscribe = window.api.onFilesChanged(() => {
      refreshNotes()
      // If active note was changed externally, reload it
      if (activeNote) {
        window.api.readNote(activeNote.path).then((content) => {
          setActiveNote((prev) => prev ? { ...prev, content } : null)
        }).catch(() => {
          // File might have been deleted
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
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
    }
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

  // Create a new note
  const createNewNote = useCallback(async (name: string) => {
    if (!vaultDir || !name.trim()) return
    const filePath = await window.api.createNote(vaultDir, name.trim())
    await refreshNotes()
    await openNote(filePath)
  }, [vaultDir, refreshNotes, openNote])

  // Delete a note
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

  // Resolve a wiki link — find note by name or create it
  const resolveLink = useCallback(async (linkName: string) => {
    const match = notes.find(
      (n) => n.name.toLowerCase() === linkName.toLowerCase()
    )
    if (match) {
      await openNote(match.path)
    } else {
      await createNewNote(linkName)
    }
  }, [notes, openNote, createNewNote])

  return {
    vaultDir,
    notes,
    activeNote,
    openNote,
    updateContent,
    createNewNote,
    deleteCurrentNote,
    changeVaultDir,
    resolveLink,
    refreshNotes,
  }
}
