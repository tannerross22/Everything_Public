import { useEffect, useRef } from 'react'
import { Editor as MilkdownEditor, rootCtx, defaultValueCtx, editorViewCtx } from '@milkdown/core'
import { TextSelection } from '@milkdown/prose/state'
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
  vaultDir?: string
}

const LINE_HEIGHT = 27 // ~1rem * 1.7 line-height

export default function Editor({ content, onChange, noteId, onLinkClick, vaultDir }: EditorProps) {
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
            if (view) view.dom.focus()
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

  return (
    <div ref={containerRef} className="editor-container">
      <div ref={editorRef} className="milkdown-wrapper" />
    </div>
  )
}
