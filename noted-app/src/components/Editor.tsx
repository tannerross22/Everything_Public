import { useEffect, useRef } from 'react'
import { Editor as MilkdownEditor, rootCtx, defaultValueCtx, editorViewCtx } from '@milkdown/core'
import { commonmark } from '@milkdown/preset-commonmark'
import { gfm } from '@milkdown/preset-gfm'
import { history } from '@milkdown/plugin-history'
import { listener, listenerCtx } from '@milkdown/plugin-listener'
import { nord } from '@milkdown/theme-nord'
import { createWikiLinkPlugin } from '../editor/wikiLinkPlugin'
import '@milkdown/theme-nord/style.css'

interface EditorProps {
  content: string
  onChange: (markdown: string) => void
  noteId: string
  onLinkClick?: (target: string) => void
}

const LINE_HEIGHT = 27 // ~1rem * 1.7 line-height

export default function Editor({ content, onChange, noteId, onLinkClick }: EditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const editorInstanceRef = useRef<MilkdownEditor | null>(null)
  const initialLoadRef = useRef(true)

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
        .config((ctx) => {
          ctx.get(listenerCtx).markdownUpdated((_ctx: any, markdown: string) => {
            if (initialLoadRef.current) {
              initialLoadRef.current = false
              return
            }
            onChange(markdown)
          })
        })
        .use(onLinkClick ? createWikiLinkPlugin(onLinkClick) : [])
        .create()

      editorInstanceRef.current = editor

      // Force focus: window.focus() restores Electron window focus after confirm(),
      // then view.focus() gives ProseMirror the cursor
      window.focus()
      setTimeout(() => {
        try {
          const view = editor.ctx.get(editorViewCtx)
          if (view) {
            view.focus()
          }
        } catch {}
      }, 50)
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

      // Only handle clicks directly on the container or wrapper, not inside editor content
      const target = e.target as HTMLElement
      if (target.closest('.ProseMirror')) return

      try {
        const view = editorInstanceRef.current.ctx.get(editorViewCtx)
        if (!view) return

        // Find where the content ends
        const proseMirrorEl = container.querySelector('.ProseMirror') as HTMLElement
        if (!proseMirrorEl) return
        const contentBottom = proseMirrorEl.getBoundingClientRect().bottom
        // Use the last child's bottom as the real content bottom
        const lastChild = proseMirrorEl.lastElementChild as HTMLElement
        const realContentBottom = lastChild
          ? lastChild.getBoundingClientRect().bottom
          : contentBottom

        const clickY = e.clientY

        // Only act if click is below existing content
        if (clickY <= realContentBottom) return

        const gap = clickY - realContentBottom
        const linesToAdd = Math.max(1, Math.round(gap / LINE_HEIGHT))

        // Insert empty paragraphs at the end of the document
        const { state } = view
        const { tr, schema } = state
        const emptyParagraph = schema.nodes.paragraph.create()
        const endPos = state.doc.content.size

        for (let i = 0; i < linesToAdd; i++) {
          tr.insert(tr.doc.content.size, emptyParagraph)
        }

        // Place cursor at the very end
        const newEnd = tr.doc.content.size
        tr.setSelection(state.selection.constructor.near(tr.doc.resolve(newEnd - 1)))
        view.dispatch(tr)
        view.focus()
      } catch {}
    }

    container.addEventListener('mousedown', handleClick)
    return () => container.removeEventListener('mousedown', handleClick)
  }, [noteId])

  return (
    <div ref={containerRef} className="editor-container">
      <div ref={editorRef} className="milkdown-wrapper" />
    </div>
  )
}
