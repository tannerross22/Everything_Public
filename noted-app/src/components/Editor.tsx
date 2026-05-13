import { useEffect, useRef } from 'react'
import { Editor as MilkdownEditor, rootCtx, defaultValueCtx } from '@milkdown/core'
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

export default function Editor({ content, onChange, noteId, onLinkClick }: EditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const editorInstanceRef = useRef<MilkdownEditor | null>(null)

  useEffect(() => {
    if (!editorRef.current) return

    const el = editorRef.current

    const createEditor = async () => {
      const editorBuilder = MilkdownEditor.make()
        .config(nord)
        .config((ctx) => {
          ctx.set(rootCtx, el)
          ctx.set(defaultValueCtx, content)
          ctx.set(listenerCtx, {
            markdown: [(_ctx: any, markdown: string) => {
              onChange(markdown)
            }],
          })
        })
        .use(commonmark)
        .use(gfm)
        .use(history)
        .use(listener)

      // Add wiki link plugin if handler provided
      if (onLinkClick) {
        const wikiPlugin = createWikiLinkPlugin(onLinkClick)
        editorBuilder.use(wikiPlugin)
      }

      const editor = await editorBuilder.create()
      editorInstanceRef.current = editor
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

  return (
    <div className="editor-container">
      <div ref={editorRef} className="milkdown-wrapper" />
    </div>
  )
}
