import { useState, useRef, useEffect } from 'react'
import type { NoteFile } from '../types'

interface SearchBarProps {
  notes: NoteFile[]
  onOpenNote: (path: string) => void
  visible: boolean
  onClose: () => void
}

interface SearchResult {
  note: NoteFile
  snippet?: string
}

export default function SearchBar({ notes, onOpenNote, visible, onClose }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (visible) {
      inputRef.current?.focus()
      setQuery('')
      setResults(notes.map((n) => ({ note: n })))
      setSelectedIndex(0)
    }
  }, [visible, notes])

  const handleSearch = async (value: string) => {
    setQuery(value)
    setSelectedIndex(0)

    if (!value.trim()) {
      setResults(notes.map((n) => ({ note: n })))
      return
    }

    const q = value.toLowerCase()

    // Name matches first
    const nameMatches: SearchResult[] = notes
      .filter((n) => n.name.toLowerCase().includes(q))
      .map((n) => ({ note: n }))

    // Content search
    const contentMatches: SearchResult[] = []
    for (const note of notes) {
      if (nameMatches.some((m) => m.note.path === note.path)) continue
      try {
        const content = await window.api.readNote(note.path)
        const lower = content.toLowerCase()
        const idx = lower.indexOf(q)
        if (idx !== -1) {
          const start = Math.max(0, idx - 30)
          const end = Math.min(content.length, idx + q.length + 30)
          const snippet = (start > 0 ? '...' : '') +
            content.slice(start, end) +
            (end < content.length ? '...' : '')
          contentMatches.push({ note, snippet })
        }
      } catch {}
    }

    setResults([...nameMatches, ...contentMatches])
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((i) => Math.min(i + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      onOpenNote(results[selectedIndex].note.path)
      onClose()
    }
  }

  if (!visible) return null

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-modal" onClick={(e) => e.stopPropagation()}>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search notes..."
          className="search-input"
        />
        <div className="search-results">
          {results.map((result, i) => (
            <div
              key={result.note.path}
              className={`search-result ${i === selectedIndex ? 'selected' : ''}`}
              onClick={() => {
                onOpenNote(result.note.path)
                onClose()
              }}
              onMouseEnter={() => setSelectedIndex(i)}
            >
              <span className="search-result-name">{result.note.name}</span>
              {result.snippet && (
                <span className="search-result-snippet">{result.snippet}</span>
              )}
            </div>
          ))}
          {results.length === 0 && query && (
            <div className="search-no-results">No results found</div>
          )}
        </div>
      </div>
    </div>
  )
}
