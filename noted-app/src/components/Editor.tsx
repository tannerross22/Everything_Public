import { useEffect, useRef, useState } from 'react'
import { Editor as MilkdownEditor, rootCtx, defaultValueCtx, editorViewCtx } from '@milkdown/core'
import { TextSelection } from '@milkdown/prose/state'
import { commonmark } from '@milkdown/preset-commonmark'
import { gfm } from '@milkdown/preset-gfm'
import { history } from '@milkdown/plugin-history'
import { listener, listenerCtx } from '@milkdown/plugin-listener'
import { nord } from '@milkdown/theme-nord'
import { createWikiLinkPlugin } from '../editor/wikiLinkPlugin'
import { spellCheckPlugin, setHunspellChecker } from '../editor/spellCheckPlugin'
import { useHunspell, onHunspellReady } from '../hooks/useHunspell'
import EditorContextMenu from './EditorContextMenu'
import '@milkdown/theme-nord/style.css'

// Register callback to set hunspell checker when ready
onHunspellReady((checker) => {
  console.log('[Editor module] Hunspell is ready, setting spell checker')
  setHunspellChecker(checker)
})

interface EditorProps {
  content: string
  onChange: (markdown: string) => void
  noteId: string
  onLinkClick?: (target: string) => void
  vaultDir?: string
}

const LINE_HEIGHT = 27 // ~1rem * 1.7 line-height

export default function Editor({ content, onChange, noteId, onLinkClick, vaultDir }: EditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const editorInstanceRef = useRef<MilkdownEditor | null>(null)
  const initialLoadRef = useRef(true)
  const suggestionCacheRef = useRef<Map<string, string[]>>(new Map())
  const { checkWord, isReady: isHunspellReady } = useHunspell()
  const checkWordRef = useRef(checkWord)

  // Keep ref updated with latest checkWord
  useEffect(() => {
    checkWordRef.current = checkWord
  }, [checkWord])

  const [contextMenu, setContextMenu] = useState<{
    x: number
    y: number
    selectedText: string
    suggestions: string[]
    wordStart: number
    wordEnd: number
  } | null>(null)

  useEffect(() => {
    if (!editorRef.current) return

    const el = editorRef.current
    initialLoadRef.current = true

    const createEditor = async () => {
      const editor = await MilkdownEditor.make()
        .config(nord)
        .config((ctx) => {
          ctx.set(rootCtx, el)
          ctx.set(defaultValueCtx, content)
        })
        .use(commonmark)
        .use(gfm)
        .use(history)
        .use(listener)
        .use(spellCheckPlugin)
        .config((ctx) => {
          ctx.get(listenerCtx).markdownUpdated((_ctx: any, markdown: string) => {
            if (initialLoadRef.current) {
              initialLoadRef.current = false
              return
            }
            // After markdown updates, convert base64 images to files
            if (vaultDir && markdown.includes('data:image')) {
              window.api.convertBase64ImagesToFiles(vaultDir, noteId, markdown).then((updatedMarkdown) => {
                if (updatedMarkdown !== markdown) {
                  onChange(updatedMarkdown)
                } else {
                  onChange(markdown)
                }
              }).catch(() => {
                onChange(markdown)
              })
            } else {
              onChange(markdown)
            }
          })
        })
        .use(onLinkClick ? createWikiLinkPlugin(onLinkClick) : [])
        .create()

      editorInstanceRef.current = editor

      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          try {
            if (editorInstanceRef.current !== editor) return
            const view = editor.ctx.get(editorViewCtx)
            if (view) {
              // Disable native spell check to avoid conflicts with custom decorations
              view.dom.setAttribute('spellcheck', 'false')
              view.dom.focus()
            }
          } catch {}
        })
      })
    }

    createEditor()

    return () => {
      if (editorInstanceRef.current) {
        editorInstanceRef.current.destroy()
        editorInstanceRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [noteId])


  // Click in empty space below content: insert empty lines to reach that point
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleClick = (e: MouseEvent) => {
      if (!editorInstanceRef.current) return

      try {
        const view = editorInstanceRef.current.ctx.get(editorViewCtx)
        if (!view) return

        const proseMirrorEl = container.querySelector('.ProseMirror') as HTMLElement
        if (!proseMirrorEl) return

        const lastChild = proseMirrorEl.lastElementChild as HTMLElement
        const realContentBottom = lastChild
          ? lastChild.getBoundingClientRect().bottom
          : proseMirrorEl.getBoundingClientRect().bottom

        // Click is within content — let ProseMirror handle it natively
        if (e.clientY <= realContentBottom) return

        // Click is below content — we handle it
        e.preventDefault()

        const gap = e.clientY - realContentBottom
        const linesToAdd = Math.max(1, Math.round(gap / LINE_HEIGHT))

        const { state } = view
        const { tr, schema } = state
        const emptyParagraph = schema.nodes.paragraph.create()

        for (let i = 0; i < linesToAdd; i++) {
          tr.insert(tr.doc.content.size, emptyParagraph)
        }

        const newEnd = tr.doc.content.size
        tr.setSelection(TextSelection.near(tr.doc.resolve(newEnd - 1)))
        view.dispatch(tr)
        view.focus()
      } catch {}
    }

    container.addEventListener('mousedown', handleClick)
    return () => container.removeEventListener('mousedown', handleClick)
  }, [noteId])

  // Context menu handler
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault()

      if (!editorInstanceRef.current) return

      // Get the editor view
      const view = editorInstanceRef.current.ctx.get(editorViewCtx)
      if (!view) return

      // Get selected text from window selection
      let selectedText = window.getSelection()?.toString() || ''
      let wordToCheck = selectedText.trim()
      let wordStart = 0
      let wordEnd = 0

      // If no selection, try to get word at cursor position
      if (!selectedText) {
        const coords = { left: e.clientX, top: e.clientY }
        const pos = view.posAtCoords(coords)

        if (pos) {
          const { doc } = view.state
          const $pos = doc.resolve(pos.pos)
          const node = $pos.parent
          const textContent = node.textContent
          const offset = $pos.parentOffset
          const nodePos = pos.pos - offset

          // Find word boundaries
          let start = offset
          let end = offset

          // Move start backwards to find word start
          while (start > 0 && /[\w']/.test(textContent[start - 1])) {
            start--
          }

          // Move end forwards to find word end
          while (end < textContent.length && /[\w']/.test(textContent[end])) {
            end++
          }

          if (start < end) {
            wordToCheck = textContent.slice(start, end)
            selectedText = wordToCheck
            wordStart = nodePos + start
            wordEnd = nodePos + end
          }
        }
      }

      // Check cache first for instant suggestions
      let suggestions: string[] = []
      const cacheKey = wordToCheck.toLowerCase()

      if (wordToCheck && !/\s/.test(wordToCheck)) {
        if (suggestionCacheRef.current.has(cacheKey)) {
          suggestions = suggestionCacheRef.current.get(cacheKey) || []
        }
      }

      // Show menu immediately with cached suggestions (or empty if not cached yet)
      setContextMenu({
        x: e.clientX,
        y: e.clientY,
        selectedText: wordToCheck,
        suggestions,
        wordStart,
        wordEnd,
      })

      // If not cached, fetch API suggestions in the background
      // (spell check plugin may have already started this, but fetch again to be sure)
      if (wordToCheck && !/\s/.test(wordToCheck) && !suggestionCacheRef.current.has(cacheKey)) {
        console.log('[handleContextMenu] Calling checkWord for:', wordToCheck)
        checkWordRef.current(wordToCheck).then((newSuggestions) => {
          console.log('[handleContextMenu] Got suggestions:', newSuggestions)
          suggestionCacheRef.current.set(cacheKey, newSuggestions)
          // Update context menu with API suggestions if it's still open
          setContextMenu((prev) => {
            if (prev && prev.selectedText === wordToCheck) {
              return { ...prev, suggestions: newSuggestions }
            }
            return prev
          })
        })
      }
    }

    container.addEventListener('contextmenu', handleContextMenu)
    return () => container.removeEventListener('contextmenu', handleContextMenu)
  }, [])

  const handleCopy = () => {
    const selected = window.getSelection()?.toString()
    if (selected) {
      navigator.clipboard.writeText(selected)
    }
  }

  const handlePaste = () => {
    if (!editorInstanceRef.current) return
    try {
      const view = editorInstanceRef.current.ctx.get(editorViewCtx)
      if (!view) return
      navigator.clipboard.readText().then((text) => {
        const { state } = view
        const { tr } = state
        const selection = state.selection
        tr.insertText(text, selection.from, selection.to)
        view.dispatch(tr)
      })
    } catch {}
  }


  const handleSelectSuggestion = (suggestion: string) => {
    if (!editorInstanceRef.current || !contextMenu) return

    try {
      const view = editorInstanceRef.current.ctx.get(editorViewCtx)
      if (!view) return

      const { state } = view
      let start = contextMenu.wordStart
      let end = contextMenu.wordEnd

      // If we have no stored positions, fall back to current selection
      if (start === 0 && end === 0) {
        const { selection } = state
        start = selection.from
        end = selection.to
      }

      const { tr } = state
      tr.insertText(suggestion, start, end)
      view.dispatch(tr)
    } catch (e) {
      console.warn('Error selecting suggestion:', e)
    }
  }

  const handleInsertLink = () => {
    if (!editorInstanceRef.current || !contextMenu) return

    try {
      const view = editorInstanceRef.current.ctx.get(editorViewCtx)
      if (!view) return

      const { state } = view
      let text = contextMenu.selectedText
      let start = contextMenu.wordStart
      let end = contextMenu.wordEnd

      // If no stored positions, try window selection
      if (!text) {
        text = window.getSelection()?.toString()
        if (!text) return
        const { selection } = state
        start = selection.from
        end = selection.to
      }

      const linked = `[[${text}]]`
      const { tr } = state
      tr.insertText(linked, start, end)
      view.dispatch(tr)
    } catch {}
  }

  return (
    <div ref={containerRef} className="editor-container">
      <div ref={editorRef} className="milkdown-wrapper" />
      {contextMenu && (
        <EditorContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          selectedText={contextMenu.selectedText}
          suggestions={contextMenu.suggestions}
          onCopy={handleCopy}
          onPaste={handlePaste}
          onSelectSuggestion={handleSelectSuggestion}
          onInsertLink={handleInsertLink}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  )
}
